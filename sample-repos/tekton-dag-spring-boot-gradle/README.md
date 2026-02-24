# tekton-dag-spring-boot-gradle

Sample Gradle Spring Boot app for [tekton-dag](https://github.com/jmjava/tekton-dag) pipeline stacks.

- **Build tool:** gradle  
- **Runtime:** spring-boot  
- **Java:** 21  

Use with stack app config: `tool: gradle`, `runtime: spring-boot`, `build-command: "./gradlew clean bootJar -x test"`. Requires `gradlew` in repo.
