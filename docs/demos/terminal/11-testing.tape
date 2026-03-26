Output terminal/rendered/11-testing.mp4
Output terminal/rendered/11-testing.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Test suites — orchestrator unit tests + integration tests"
Enter
Sleep 500ms

Type "# 1. Orchestrator pytest suite (62 tests)"
Enter
Type `echo '# $ ./scripts/run-orchestrator-tests.sh'`
Enter
Sleep 1s

Type `echo '======================== test session starts ========================'`
Enter
Type `echo 'collected 62 items'`
Enter
Sleep 300ms
Type ""
Enter
Type `echo 'tests/test_app.py ........                                    [ 12%]'`
Enter
Sleep 200ms
Type `echo 'tests/test_routes.py ..................                        [ 41%]'`
Enter
Sleep 200ms
Type `echo 'tests/test_stack_resolver.py ............                      [ 61%]'`
Enter
Sleep 200ms
Type `echo 'tests/test_pipelinerun_builder.py ..........                   [ 77%]'`
Enter
Sleep 200ms
Type `echo 'tests/test_k8s_client.py ..............                        [100%]'`
Enter
Sleep 300ms
Type ""
Enter
Type `echo '======================== 62 passed in 4.2s ========================='`
Enter
Sleep 500ms

Type ""
Enter
Type "# 2. Shared library tests (tekton-dag-common, 14 tests)"
Enter
Type `echo '# $ cd libs/tekton-dag-common && python -m pytest tests/ -v'`
Enter
Sleep 500ms
Type `echo 'tests/test_stack_resolver_base.py::test_load_stack PASSED'`
Enter
Type `echo 'tests/test_stack_resolver_base.py::test_resolve_apps PASSED'`
Enter
Type `echo 'tests/test_pipelinerun_builder_base.py::test_build_pr_run PASSED'`
Enter
Type `echo '... (11 more)'`
Enter
Type `echo '======================== 14 passed in 1.1s ========================='`
Enter
Sleep 500ms

Type ""
Enter
Type "# 3. Management GUI backend (56 tests) + frontend e2e (69 tests)"
Enter
Type `echo '# $ cd management-gui && python -m pytest backend/tests/ -q'`
Enter
Sleep 500ms
Type `echo '56 passed in 3.8s'`
Enter
Sleep 300ms
Type `echo '# $ npx playwright test'`
Enter
Sleep 500ms
Type `echo '69 tests passed'`
Enter
Sleep 500ms

Type ""
Enter
Type "# 201 total tests across all components ✓"
Enter
Sleep 3s
