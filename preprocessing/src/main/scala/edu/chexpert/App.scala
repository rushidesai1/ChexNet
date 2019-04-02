package com.edu.chexpert

import java.awt.RenderingHints
import java.awt.geom.AffineTransform
import java.awt.image.{AffineTransformOp, BufferedImage, DataBufferByte, RescaleOp}
import java.io.File

import edu.chexpert.helper.SparkHelper
import javax.imageio.ImageIO
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.Row

case class ImageRow(file:String,width:Int,height:Int,channels:Int=1,data:Array[Byte])

object App {



  def zeroMean(arr:Array[Byte]):Array[Byte]={
    val mean=arr.map(_.toInt).sum/arr.length

    val std=Math.sqrt(arr.map(x=>(x.toInt - mean)*(x.toInt - mean)).sum/arr.length)

    arr.map(x=>(x-mean)).map(_.toByte)

  }

  def asVector(img:BufferedImage)={
    var arr:Array[Byte]=img.getRaster.getDataBuffer.asInstanceOf[DataBufferByte].getData

    val testDouble = arr.map(x=>x.toDouble).to[scala.Vector].toArray
    Vectors.dense(testDouble)
  }


  def mapOutputLocation(imagePath:String):String={
    imagePath.substring(imagePath.lastIndexOf("/")+1)

  }
  //Now just writing to local file , will update later
  def saveImage(img:BufferedImage,output:String="output.jpg"): Unit ={
    ImageIO.write(img, "jpg", new File(output))
  }

  def adjustPixel(img:BufferedImage,scaleFactor:Float,offset:Float)={

    val res = new BufferedImage(img.getWidth, img.getHeight, BufferedImage.TYPE_BYTE_GRAY)

    val rescaleOp = new RescaleOp(scaleFactor, offset, null)
    rescaleOp.filter(img, res)

    res
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

    ImageRow(origin,width,height,1,zeroMean(image1Dta))
  }



  def flipBufferedImage(bufferedImage:BufferedImage):BufferedImage={

    val tx = AffineTransform.getScaleInstance(-1, 1)
    tx.translate(-bufferedImage.getWidth(null), 0)
    val op = new AffineTransformOp(tx, AffineTransformOp.TYPE_NEAREST_NEIGHBOR)
    return op.filter(bufferedImage, null)
  }




  def main(args: Array[String]): Unit = {


    val spark = SparkHelper.spark
    val sc = spark.sparkContext


    //load images
    spark.read.format("image")
      .option("dropInvalid", true)
      .load("images").createOrReplaceTempView("images")


    val images: RDD[ImageRow] =spark.sql("select image.origin,image.width,image.height,image.nChannels, image.mode , image.data from images")
      .rdd.map(asImageRow(_))

   val res=images.map(i=>(i,asBufferedImage(i))).map{case (ir,b)=>(ir,resizeBufferedImage(b,244,244))}.
     map{case (ir,b)=>(ir,flipBufferedImage(b))}.
     map{case (ir,b)=>saveImage(b,mapOutputLocation(ir.file))}.count()

   sc.stop()
  }

}
