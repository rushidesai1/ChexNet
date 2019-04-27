package com.edu.chexpert

import java.awt.RenderingHints
import java.awt.geom.AffineTransform
import java.awt.image.{AffineTransformOp, BufferedImage, DataBufferByte, RescaleOp}
import java.io.{ByteArrayOutputStream, File}


import edu.chexpert.helper.SparkHelper
import javax.imageio.ImageIO
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.Row



case class ImageRow(file:String,width:Int,height:Int,channels:Int=1,data:Array[Byte])
case class Label(Path:String,
                  Sex:String,
                  Age:String,
                  `Frontal/Lateral`:String,
                 `AP/PA`:String,
                  `No Finding`:String,
                  `Enlarged Cardiomediastinum`:String,
                  Cardiomegaly:String,
                  `Lung Opacity`:String,
                  `Lung Lesion`:String,
                  Edema:String,
                  Consolidation:String,
                  Pneumonia:String,
                  Atelectasis:String,
                  Pneumothorax:String,
                  `Pleural Effusion`:String,
                  `Pleural Other`:String,
                  Fracture:String,
                  `Support Devices`:String)


case class ChexImage(bufferedImage: BufferedImage,label: Label)
case class ImageText(id:String,bytes:String)


object App {


  def dropPrefix(s:String,pre:String):String={
    val trimmed=s.substring(s.indexOf(pre))
    trimmed.replaceAll(pre,"")
  }


  //Now just writing to local file , will update later
  def saveImage(img:BufferedImage,output:String="output.jpg"): Unit ={
    ImageIO.write(img, "jpg", new File(output))
  }


  def resizeBufferedImage(img:BufferedImage,targetWidth:Int,targetHeight:Int):BufferedImage={

    import java.awt.image.BufferedImage
    val res = new BufferedImage(targetWidth, targetHeight, img.getType)

    val graphics2D=res.createGraphics
    graphics2D.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
    graphics2D.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)
    graphics2D.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)

    graphics2D.drawImage(img, 0, 0, targetWidth, targetHeight, null)


    return res
  }

  def asBufferedImage(imgRow:ImageRow):BufferedImage={
    val img = new BufferedImage(imgRow.width, imgRow.height, BufferedImage.TYPE_BYTE_GRAY)

    var pos=0
    for (y <-  0 until  imgRow.height){
      for (x <- 0 until imgRow.width) {
        img.getRaster().setSample(x, y, 0, imgRow.data(pos))
        pos+=1
      }
    }
    return img

  }

  def asImageRow(row:Row):ImageRow={
    val origin=row.getAs[Any]("origin").asInstanceOf[String]

    val width=row.getAs[Any]("width").asInstanceOf[Int]
    val height=row.getAs[Any]("height").asInstanceOf[Int]
    val image1Dta:Array[Byte]=row.getAs[Any]("data").asInstanceOf[Array[Byte]]

    ImageRow(origin,width,height,1,image1Dta)
  }



  def flipBufferedImage(bufferedImage:BufferedImage):BufferedImage={

    val tx = AffineTransform.getScaleInstance(-1, 1)
    tx.translate(-bufferedImage.getWidth(null), 0)
    val op = new AffineTransformOp(tx, AffineTransformOp.TYPE_NEAREST_NEIGHBOR)
    return op.filter(bufferedImage, null)
  }

  def bufferedAsText(bufferedImage: BufferedImage, separator:String=" "):String={
    import javax.imageio.ImageIO
    val baos = new ByteArrayOutputStream()
    ImageIO.write(bufferedImage, "jpg", baos)
    baos.flush
    val imageInByte: Array[Byte] = baos.toByteArray
    return imageInByte.map(_.toString).mkString(separator)

  }




  def main(args: Array[String]): Unit = {


    val spark = SparkHelper.spark
    val sc = spark.sparkContext


    import spark.implicits._



    //load images
    spark.read.format("image")
      .option("dropInvalid", true)
      .load("images/input/train/*/*").createOrReplaceTempView("images")


    val images: RDD[ImageRow] =spark.sql("select image.origin,image.width,image.height,image.nChannels, image.mode , image.data from images")
      .rdd.map(asImageRow(_))

    val labels= spark.read.format("csv").option("header", "true").load("labels/train.csv").as[Label].rdd
    val labelsPrefix="input/train/"

    val adjustedImages=images.map(i=>i.copy(file = dropPrefix(i.file,labelsPrefix) )).map(i=>(i.file,i))

    val adjustedLabels=labels.map(l=>l.copy(Path = dropPrefix(l.Path,labelsPrefix))).map(l=>(l.Path,l))

    val data: RDD[ChexImage] =adjustedImages.join(adjustedLabels).map{case (path,(imageRow,label))=>ChexImage(asBufferedImage(imageRow),label)}

    val resized: RDD[ChexImage] =data.map(i=>i.copy(bufferedImage = resizeBufferedImage(i.bufferedImage,224,244)))

    val flipped: RDD[ChexImage] =resized.map(i=>i.copy(bufferedImage = flipBufferedImage(i.bufferedImage)))

    val output=resized.union(flipped).zipWithIndex()

    //save labels
    output.map(o=>o._1.label.copy(Path = o._2.toString)).repartition(1).toDS().write.format("csv").option("header", "true").save("output/labels")

    //save images as text
    output.map(o=>o._2.toString +" "+ bufferedAsText(o._1.bufferedImage)).toDS().write.format("text").save("output/images/txt")

    //save images as jpg (only works for local , will break for hdfs or s3
    val dir="output/images/jpg/"
    new File(dir).mkdirs()
    output.map(o=>saveImage(o._1.bufferedImage,dir+o._2.toString+".jpg")).count()

   sc.stop()
  }

}
