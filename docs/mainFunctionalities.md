#AM main Functionalities

-	React to Failures: Retry if failure happens or apply corrective measures 
-	Monitor Processes/Metadata/Information: Success or failure status
-	Check Dependencies:
	*	Data dependencies: e.g. upstream data is missing
	*	Execution dependencies: e.g. job 2 run after job 1 is finished
-	Scale its functionalities
-	Automatic Deployment: Deploy new changes constantly (e.g. update ML model)
-	Store data: To create historical datasets 
-	Process historic data/ETL: Supported with integration of Apache Nifi
-	Orchestrator: Invoke Human in the loop - HITL (ask for validation, feedback, labelling, etc.) OR Return feedback to AI Methods 