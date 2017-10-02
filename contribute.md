How to contribute
=================

## Writing an issue

By writing an issue, you're already contributing a lot. Though, if you want to really help us, try to be clear when you 
write this issue : state your machine, the version of the app you are using (git sha and branch, pip version if available),
give us the specific error and means to replicate it (attach any corpus sample that might be of interest. You do not need to 
give us the full data!), and ensure to give a proper pip freeze result, just in case.

Try to write your issue (if this is a bug you describing) by adding separation such as

```markdown
## Context of the issue
Description of steps to take to replicate the issue

## Expected output
Output that would normally happen

## Effective output
Output that you have

## Error code (if applicable)

## Environment
Pip freeze, ubuntu version, anything useful
```

Think about running your app in debug mode if you can ! That will help us with a nice debug info !

## Writing a test

For writing and running test, we recommend you install chromium-webdriver (`apt-get install chromium-chromedriver`). 
Make sure to have the full requirements.txt installed (this includes packages needed to run the tests)

### Integration tests

If you want to write a test that would follow human behaviour, you will need to write a test using selenium. This kind of
tests are in the module `tests.test_selenium`.

#### New class of test

#### New method of test

### Tests about models or API
