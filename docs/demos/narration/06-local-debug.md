What happens when a test fails in the pull-request pipeline and you need to debug? You do not SSH into a pod or add print statements. You debug locally — with your IDE, your breakpoints, your tools — while connected to the live cluster.

tekton-dag includes a mirrord build image specifically for this workflow. On the left side of the screen, you see a developer's laptop running their IDE. On the right, the Kubernetes cluster running the full stack. Between them, mirrord creates a secure tunnel.

When you run mirrord exec, it intercepts network traffic destined for your service's pod and mirrors it to your local process. Your local code receives real requests from the cluster — real headers, real payloads, real downstream service calls.

Watch — a request enters the cluster through the front-end. The mirrord agent intercepts it and redirects it to the developer's machine. The IDE hits a breakpoint. The developer steps through the code line by line, inspects variables, examines the call stack — all with live cluster data flowing through.

This is not a mock environment. The request originated from the Vue front-end in the cluster, traveled through the Spring Boot BFF, and arrived at your local machine because mirrord redirected the traffic. Database connections, downstream API calls, environment variables — everything is real.

The pipeline even supports this during pull-request testing. Because the intercept setup is already wired, you can attach mirrord to the pull-request pod to debug a failing test with the exact request that caused the failure.

When you are done debugging, mirrord disconnects cleanly. Traffic returns to the cluster pod. No artifacts left behind, no configuration to undo.

Local IDE. Live cluster data. Full breakpoint debugging. That is the developer experience tekton-dag enables.
