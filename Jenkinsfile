pipeline {
    agent { label 'dc16nix2p16'}
       options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timeout(time: 3, unit: 'HOURS')
       }
       environment {
           REPOSITORY = 'abalpha-kalotay-pricer'
           DEV_VAULT = 'kv-fiquantit-dev-001'
           DEV_REGISTRY_NAME = 'acrfiquantitdev001'
           QA_REGISTRY_NAME = 'acrfiquantitqa001'
           PROD_REGISTRY_NAME = 'acrfiquantitprod001'
           AZ_SPN_USERNAME_DEV = credentials('fi-az-spn-username-dev')
           AZ_SPN_PWD_DEV = credentials('fi-az-spn-password-dev')
           AZ_SPN_USERNAME_QA = credentials('fi-az-spn-username-qa')
           AZ_SPN_PWD_QA = credentials('fi-az-spn-password-qa')
           AZ_TENANT_ID = credentials('fi-az-tenant-id')

           AZ_SPN_USERNAME_PROD = credentials('fi-az-spn-username-prod')
           AZ_SPN_PWD_PROD = credentials('fi-az-spn-password-prod')
       }

    stages {
        stage('Copy Keys') {
            when {
                anyOf {
                    branch 'kalotay';
                }
            }
            steps {
                sh ''' chmod 755 -R ./${REPOSITORY}/
                             ./${REPOSITORY}/copy_keys.sh'''
            }
        }

        stage('Build Container'){
            when {
                anyOf {
                    branch 'kalotay';
                }
            }
            steps {
                sh ''' source /etc/profile.d/proxy.sh
                       az account clear
                       az login --service-principal -username $AZ_SPN_USERNAME_PROD -password $AZ_SPN_PWD_PROD --tenant $AZ_TENANT_ID
                       az account set --subscription "f91f2bd7-c90a-4b12-93cb-289573253eed"
                       az acr login --name $PROD_REGISTRY_NAME --username $AZ_SPN_USERNAME_PROD --password $AZ_SPN_PWD_PROD
                       make build
                    '''
            }
        }

        stage('Push Image to PROD ACR'){
            when {
                anyOf {
                    branch 'kalotay';
                }
            }
            steps {
                sh ''' 
                        echo ${BUILD_NUMBER}
                        source /etc/profile.d/proxy.sh
                        az account clear
                        az login --service-principal -username $AZ_SPN_USERNAME_PROD -password $AZ_SPN_PWD_PROD --tenant $AZ_TENANT_ID
                        az account set --subscription "f91f2bd7-c90a-4b12-93cb-289573253eed"
                        az acr login --name $PROD_REGISTRY_NAME --username $AZ_SPN_USERNAME_PROD --password $AZ_SPN_PWD_PROD
                        make push
                    '''
            }
        }

        stage('Deploy application to AKS'){
            when {
                anyOf {
                    branch 'kalotay';
                }
            }
            steps {
                sh ''' 
                        echo ${BUILD_NUMBER}
                        source /etc/profile.d/proxy.sh
                        az account clear
                        az login --service-principal -username $AZ_SPN_USERNAME_PROD -password $AZ_SPN_PWD_PROD --tenant $AZ_TENANT_ID
                        az account set --subscription "f91f2bd7-c90a-4b12-93cb-289573253eed"
                        az aks get-credentials --resource-group fiquantit-prod-rg --name fiquantit-prod-aks
                        make deploy_aks
                    '''
            }
        }

    }

    post {
        always {
            emailext body: "Build Status: ${currentBuild.currentResult}: Job ${JOB_NAME} build ${BUILD_NUMBER} has finished. Check console output at ${BUILD_URL}",
            to: ""
            subject: "Jenkins Build ${currentBuild.currentResult}: ${JOB_NAME} #${BUILD_NUMBER}"
        }
    }

}