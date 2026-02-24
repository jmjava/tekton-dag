# Step debugging with Telepresence intercept

Use these launch configs when you want to **step-debug an app** while traffic is sent to your local process via a Telepresence intercept (separate from the PR pipeline flow).

## Flow

1. **Start the app with the debugger**  
   In the Run and Debug view, pick the config for the app (e.g. **Vue (demo-fe): Launch & debug** or **Spring Boot (demo-api): Attach**).

2. **Create the intercept**  
   In a terminal (with `telepresence connect` already run):
   ```bash
   telepresence intercept <service-name> -n staging --port <local-port>
   ```
   Examples:
   - `telepresence intercept demo-fe -n staging --port 3000`
   - `telepresence intercept release-lifecycle-demo -n staging --port 8080`
   - `telepresence intercept demo-api -n staging --port 8080`
   - `telepresence intercept notifications-svc -n staging --port 5000`

3. **Set breakpoints and trigger traffic**  
   Hit the app (browser, curl, or another service in the stack); the debugger will stop at breakpoints.

## Workspace folders

Launch configs use **workspace folder** paths (e.g. `${workspaceFolder:tekton-dag-vue-fe}`). Add each app repo as a workspace folder with these names:

- `tekton-dag-vue-fe`
- `tekton-dag-spring-boot`
- `tekton-dag-spring-boot-gradle`
- `tekton-dag-spring-legacy`
- `tekton-dag-flask`
- `tekton-dag-php`

(File → Add Folder to Workspace → choose each repo; the folder name in the workspace should match the list above.)

## Configs by app

| App (stack name)     | Launch / Attach | Port(s) |
|----------------------|-----------------|--------|
| demo-fe (Vue)        | Launch or Attach (Node) | 3000, debug 9229 |
| release-lifecycle-demo (Spring Boot) | Launch or Attach (Java) | 8080, debug 5005 |
| demo-api (Spring Boot Gradle) | Launch or Attach (Java) | 8080, debug 5005 |
| internal-api (Spring Legacy) | Attach only (Java) | 8080, debug 5005 |
| notifications-svc (Flask) | Launch or Attach (Python) | 5000, debugpy 5678 |
| vendor-adapter (PHP) | Listen for Xdebug | 9003; run `php -S 0.0.0.0:8000` in app dir |

## Java apps (Spring Boot / Gradle / Legacy)

- **Launch**: Uses the app workspace folder; the Java extension will resolve the project from that folder.
- **Attach**: Start the app from a terminal (in the app’s workspace folder) with a debug port, then attach:
  ```bash
  mvn spring-boot:run -Dspring-boot.run.jvmArguments="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005"
  ```
  Then run **Spring Boot (release-lifecycle-demo): Attach** in VSCode.

## PHP

Start the built-in server in the **tekton-dag-php** workspace folder (with Xdebug configured to connect to port 9003), then run **PHP (vendor-adapter): Listen for Xdebug** before sending requests.

## Flask (attach)

To use **Flask: Attach**, start the app with debugpy listening from the **tekton-dag-flask** folder:
```bash
python -m debugpy --listen 5678 -m flask run --host=0.0.0.0 --port=5000
```
