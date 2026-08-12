# Activity-Based model for Montpellier using Matsim.

Step number one is to assemble the project in Maven "target" folder should appear afterwards: `mvn clean package`

Command to run the simulation:

```
java -Xmx2g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
run --config=scenarios/equil/config-2026.xml
```

MATSim version: `2026.0`

Java compiler version: `25`
