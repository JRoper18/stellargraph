#!/bin/bash

set -xeo pipefail

junit_file="junit-${BUILDKITE_JOB_ID}.xml"

upload_tests() {
  buildkite-agent artifact upload "$junit_file" "s3://${AWS_LOGS_BUCKET}/pytest/${BUILDKITE_BRANCH}/${BUILDKITE_BUILD_NUMBER}"
}

echo "--- installing dependencies"
pip install -q --no-cache-dir '.[test]'

echo "--- listing dependency versions"
pip freeze

echo "+++ running tests"
exitCode=$?
py.test -ra --cov=stellargraph tests/ --doctest-modules --cov-report=xml -p no:cacheprovider --junitxml="./${junit_file}" || exitCode=$?

echo "--- :coverage::codecov::arrow_up: uploading coverage to codecov.io"
bash <(curl https://codecov.io/bash)

if [ "${BUILDKITE_BRANCH}" = "develop" ] || [ "${BUILDKITE_BRANCH}" = "master" ]; then
  echo "--- uploading JUnit"
  upload_tests
fi

# upload the JUnit file for the junit annotation plugin
buildkite-agent artifact upload "${junit_file}"

exit "$exitCode"
