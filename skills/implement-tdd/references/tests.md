# Single-file test commands by language

Run only the test for the current file. Replace `<file>` with the actual path.

| Language | Command |
|---|---|
| TypeScript/JavaScript (Jest) | `npx jest <file>` |
| Python/pytest | `python -m pytest <file> -v` |
| Go | `go test -v -run Test<Func> ./<pkg-dir>` (go test accepts directories, not single files) |
| Java/JUnit | `mvn -Dtest=<Class>#<method> test` |
| Ruby/RSpec | `rspec <file>` |
| Rust | `cargo test -- <module>::<test>` |
| PHP/Pest | `./vendor/bin/pest <file>` |
| C#/xUnit | `dotnet test --filter "FullyQualifiedName~<TestClass>"` |
| Dart | `dart test <file>` |
