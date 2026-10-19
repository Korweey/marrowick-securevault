-- Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
-- Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
-- File: sql/03_cloudtrail_audit.sql – Athena table over CloudTrail logs + audit questions
-- Run each statement on its own in Athena.

-- 1) Separate database for audit data (keeps it apart from analyst data)
CREATE DATABASE IF NOT EXISTS marrowick_audit;

-- 2) CloudTrail table with partition projection (no crawler / MSCK REPAIR needed)
CREATE EXTERNAL TABLE marrowick_audit.cloudtrail_logs (
  eventversion STRING,
  useridentity STRUCT<
    type:STRING, principalid:STRING, arn:STRING, accountid:STRING, invokedby:STRING,
    accesskeyid:STRING, username:STRING,
    sessioncontext:STRUCT<
      attributes:STRUCT<mfaauthenticated:STRING, creationdate:STRING>,
      sessionissuer:STRUCT<type:STRING, principalid:STRING, arn:STRING, accountid:STRING, username:STRING>>>,
  eventtime STRING,
  eventsource STRING,
  eventname STRING,
  awsregion STRING,
  sourceipaddress STRING,
  useragent STRING,
  errorcode STRING,
  errormessage STRING,
  requestparameters STRING,
  responseelements STRING,
  additionaleventdata STRING,
  requestid STRING,
  eventid STRING,
  resources ARRAY<STRUCT<arn:STRING, accountid:STRING, type:STRING>>,
  eventtype STRING,
  apiversion STRING,
  readonly STRING,
  recipientaccountid STRING,
  serviceeventdetails STRING,
  sharedeventid STRING,
  vpcendpointid STRING
)
PARTITIONED BY (region STRING, `timestamp` STRING)
ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://aws-cloudtrail-logs-004716017211-36c99747/AWSLogs/004716017211/CloudTrail/'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.region.type'='enum',
  'projection.region.values'='us-east-1',
  'projection.timestamp.type'='date',
  'projection.timestamp.format'='yyyy/MM/dd',
  'projection.timestamp.range'='2026/10/18,NOW',
  'projection.timestamp.interval'='1',
  'projection.timestamp.interval.unit'='DAYS',
  'storage.location.template'='s3://aws-cloudtrail-logs-004716017211-36c99747/AWSLogs/004716017211/CloudTrail/${region}/${timestamp}'
);

-- 3) Sanity check: events are arriving
SELECT eventsource, count(*) AS events
FROM marrowick_audit.cloudtrail_logs
GROUP BY eventsource ORDER BY events DESC;

-- Q1) WHO ACCESSED THE CURATED CLINIC-C DATA? (S3 data events on curated/clinic-c/)
SELECT eventtime,
       useridentity.arn                                   AS who,
       useridentity.invokedby                             AS via_service,
       eventname,
       json_extract_scalar(requestparameters, '$.key')    AS object_key,
       sourceipaddress
FROM marrowick_audit.cloudtrail_logs
WHERE eventsource = 's3.amazonaws.com'
  AND json_extract_scalar(requestparameters, '$.bucketName') = 'marrowick-curated-004716017211'
  AND json_extract_scalar(requestparameters, '$.key') LIKE 'clinic-c/%'
ORDER BY eventtime;

-- Q2) WHAT API CALLS MODIFIED BUCKET POLICIES / BUCKET SECURITY SETTINGS?
SELECT eventtime,
       useridentity.arn                                       AS who,
       eventname,
       json_extract_scalar(requestparameters, '$.bucketName') AS bucket,
       sourceipaddress,
       errorcode
FROM marrowick_audit.cloudtrail_logs
WHERE eventsource = 's3.amazonaws.com'
  AND eventname IN ('PutBucketPolicy', 'DeleteBucketPolicy', 'PutBucketEncryption',
                    'DeleteBucketEncryption', 'PutBucketPublicAccessBlock', 'PutBucketVersioning')
ORDER BY eventtime;

-- Q3 (anomaly detection) DENIED / UNAUTHORIZED ATTEMPTS
SELECT eventtime, useridentity.arn AS who, eventsource, eventname, errorcode,
       substr(errormessage, 1, 140) AS error_message
FROM marrowick_audit.cloudtrail_logs
WHERE errorcode IN ('AccessDenied', 'AccessDeniedException', 'UnauthorizedOperation', 'Client.UnauthorizedOperation')
ORDER BY eventtime DESC
LIMIT 50;

-- Q3b) DENIED ATTEMPTS, CONSOLE NOISE REMOVED (focus on data/security services)
-- Console pages make background read calls (notifications, resource-explorer, uxc, datazone...)
-- that are denied in the Learner Lab and drown out real signals.
SELECT eventtime, useridentity.arn AS who, eventsource, eventname, errorcode,
       substr(errormessage, 1, 140) AS error_message
FROM marrowick_audit.cloudtrail_logs
WHERE errorcode IN ('AccessDenied', 'AccessDeniedException', 'UnauthorizedOperation', 'Client.UnauthorizedOperation')
  AND eventsource IN ('s3.amazonaws.com', 'iam.amazonaws.com', 'kms.amazonaws.com',
                      'lakeformation.amazonaws.com', 'glue.amazonaws.com', 'states.amazonaws.com')
ORDER BY eventtime;
