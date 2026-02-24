FROM tomcat:10-jre17-temurin-jammy
# Remove default webapps; deploy our WAR as ROOT
RUN rm -rf /usr/local/tomcat/webapps/*
COPY target/*.war /usr/local/tomcat/webapps/ROOT.war
EXPOSE 8080
CMD ["catalina.sh", "run"]
