/* SimpleApp.scala */
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

object SimpleApp {
  def main(args: Array[String]) {

    val inputDir = "input/"
    // val inputFile = inputDir + "test_text_file.txt"
    // val outputFile = inputDir + "test_output.txt"

    val inputFile = "s3://team10-chestxray/tutorialEMR/input/test_text_file.txt"
    val outputFile = "s3://team10-chestxray/tutorialEMR/output/test_output.txt"

    val conf = new SparkConf().setAppName("Simple Application")
    val sc = new SparkContext(conf)

    // val names: List[String] = List("Doug", "Eileen", "Doug", "Cam", "Kirk", "Brooke", "Aaron", "Adam")

    val logData = sc.textFile(inputFile, 2).cache()
    // val logData = sc.parallelize(names).cache()

    val letter1 = "a"
    val letter2 = "e"
    val letter3 = "i"
    val letter4 = "o"
    val letter5 = "u"

    val num1s = logData.filter(line => line.contains(letter1)).count()
    val num2s = logData.filter(line => line.contains(letter2)).count()
    val num3s = logData.filter(line => line.contains(letter3)).count()
    val num4s = logData.filter(line => line.contains(letter4)).count()
    val num5s = logData.filter(line => line.contains(letter5)).count()

    println()
    println("--------------------------------------------------")

    println("Lines with %s: %s".format(letter1, num1s))
    println("Lines with %s: %s".format(letter2, num2s))
    println("Lines with %s: %s".format(letter3, num3s))
    println("Lines with %s: %s".format(letter4, num4s))
    println("Lines with %s: %s".format(letter5, num5s))

    println("--------------------------------------------------")
    println()

    // Try to write to S3
    val headerRDD= sc.parallelize(Seq("HEADER"))

    // Replace BODY part with your DF
    val bodyRDD= sc.parallelize(Seq("Brooke", "Kirk", "Cam", "Doug", "Aaron", "Adam"))

    val footerRDD = sc.parallelize(Seq("FOOTER"))

    //combine all rdds to final
    val finalRDD = headerRDD ++ bodyRDD ++ footerRDD

    //finalRDD.foreach(line => println(line))

    // output to one file
    finalRDD.repartition(1).saveAsTextFile(outputFile)

    // Stop Spark and finish
    sc.stop()
  }
}
