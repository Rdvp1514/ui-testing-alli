pipeline {
    agent any
    stages {
    stage('Installing') {
            steps {
                echo 'Installing...'
                dir('') {
                withEnv(["HOME=${env.WORKSPACE}/"]) {
                sh 'pip3 install -r requirements.txt'
                }
                }
            }
        }
        stage('All Tests...') {
            steps {
                echo 'Run all Tests...'
                dir('') {
                withEnv(["HOME=${env.WORKSPACE}/"]) {
                sh 'python3 Runner.py'
                }
                }
            }
        }

    }
}