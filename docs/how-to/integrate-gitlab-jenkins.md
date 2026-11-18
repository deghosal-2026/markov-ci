# How-to: integrate with GitLab CI and Jenkins

The engine is a CLI (F10); anything that can run a shell step can run markov-ci. The
GitHub Action (F15) is just a wrapper — GitLab and Jenkins get the same guarantees via
the exit-code contract (spec 0008, ADR-0017): `0 = a1` · `1 = a2` · `2 = usage error` ·
`3 = a3` · `4 = invalid` · `5 = internal`.

## GitLab CI

```yaml
# .gitlab-ci.yml
markov-govern:
  stage: test
  image: python:3.12
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - pip install markov-ci
    - pytest tests/unit --junitxml=report.xml || true
    - |
      code=0
      markov-ci run .markov-ci/config.yaml --junit report.xml --seed 42 || code=$?
      case $code in
        0) echo "a1: ready for human review" ;;
        1) echo "a2: escalated to author"; exit 1 ;;
        3) echo "a3: budget exceeded"; exit 1 ;;
        4) echo "invalid config"; exit 1 ;;
        5) echo "internal failure"; exit 1 ;;
      esac
  artifacts:
    paths: [.markov-ci/events.jsonl]
```

Notes:

- `exit 1` on `a2` is a *policy choice* — some teams allow escalate-to-author to pass
  with a warning; budgets (`a3`) should always fail.
- Upload `events.jsonl` as an artifact — it is your `recompute` input and audit trail.
- Run governed jobs on a runner tag matching your **burst pool** so agent loops never
  compete with human pipelines for warm runners (see
  [queueing](../explanations/queueing-theory.md) §4).

## Jenkins (declarative)

```groovy
pipeline {
  agent { label 'markov-burst' }        // burst pool label
  stages {
    stage('s0 — fast checks') {
      steps { sh 'pytest tests/unit --junitxml=report.xml || true' }
    }
    stage('govern') {
      steps {
        sh '''
          pip install markov-ci
          markov-ci run .markov-ci/config.yaml --junit report.xml --seed 42
        '''
      }
      post {
        always { archiveArtifacts artifacts: '.markov-ci/events.jsonl' }
      }
    }
  }
}
```

## What transfers automatically

Everything that lives in the engine, not the platform:

- deterministic triage before any agent runs (infra flakes → `a2`, zero tokens);
- policy budgets/caps/confidence — absorption guaranteed wherever the CLI runs;
- guardrails: allowlists, TMR hard-stop, isolated `ai-fix/*` branches, no auto-merge;
- the telemetry contract — same events, same `recompute`, any CI.

What's GitLab/Jenkins-specific is only plumbing: secret wiring for live harness
adapters, artifact paths, and runner-pool labels.
