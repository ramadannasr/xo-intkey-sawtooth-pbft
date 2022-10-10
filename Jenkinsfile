/*
 * Copyright 2018 Bitwise IO, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * -----------------------------------------------------------------------------
 */

pipeline {
 agent any
    options {
        timestamps()
    }

environment {
        ISOLATION_ID = sh(returnStdout: true, script: 'printf $BUILD_TAG | sha256sum | cut -c1-64').trim()
        JENKINS_UID = sh(returnStdout: true, script: "id -u ${USER}").trim()
    }

    stages {
        stage('Build xo-intkey-sawtooth-pbft') {
            steps {
                sh 'docker-compose -f docker/compose/pbft-build.yaml up'
            }
            post {
                always {
                    sh 'docker-compose -f docker/compose/pbft-build.yaml down'
                }
            }
        }

        stage('Run Unit & Integration Tests') {
            steps {
                sh 'docker-compose run --rm sawtooth-pbft cargo test'
            }
        }


        stage('Run Liveness Tests') {
            steps {
                sh './bin/run_docker_test tests/test_liveness.yaml'
            }
        }
    }

    post {
        always {
            sh 'docker-compose down'
            sh 'docker ps -aq | xargs docker stop | xargs docker rm'
        }
        aborted {
            error "Aborted, exiting now"
        }
        failure {
            error "Failed, exiting now"
        }
    }
}
