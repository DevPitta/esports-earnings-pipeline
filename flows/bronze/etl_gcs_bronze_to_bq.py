from prefect import flow, task

import pyspark
from pyspark.sql import SparkSession
from prefect_gcp.cloud_storage import GcsBucket


@task()
def extract_from_gcs(dataset_file: str) -> str:
    """Download data from GCS"""
    gcs_path = f"data/bronze/{dataset_file}"
    local_path = ""
    gcs_block = GcsBucket.load("esports")
    gcs_block.get_directory(
        from_path=gcs_path,
        local_path=local_path
    )

    return gcs_path


@task()
def wite_to_bq(spark: pyspark, path: str, df_name: str) -> None:
    """write DataFrame to BigQuery"""
    df = spark.read.format('parquet').load(path)
    df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option('table', f'esports_bronze.{df_name}') \
            .mode('overwrite') \
            .save()


@flow()
def etl_gcs_bronze_to_bq():
    """The main ETL function"""  
    
    # Create a SparkSession
    spark = SparkSession.builder \
        .appName("esports_tournaments_bronze") \
        .config("spark.executor.memory", "64g") \
        .config("spark.jars", "spark-bigquery-with-dependencies_2.12-0.34.0.jar") \
        .getOrCreate()
    
    dfs_name = ['esports_tournaments',
                'esports_games_genre',
                'esports_games_awarding_prize_money'
                ]

    for df_name in dfs_name:
        path = extract_from_gcs(df_name)
        wite_to_bq(spark, path, df_name)
    
    # End spark session    
    spark.stop()


if __name__ == '__main__':
    etl_gcs_bronze_to_bq()