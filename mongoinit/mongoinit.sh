#!/usr/bin/env bash

echo '##MONGODB init script: creating application user and db'
mongo ${MONGODB_DATABASE} \
        --host localhost \
        --port 27017 \
        -u ${MONGO_INITDB_ROOT_USERNAME} \
        -p ${MONGO_INITDB_ROOT_PASSWORD} \
        --authenticationDatabase admin \
        --eval "db.createUser({user: '${MONGO_NON_ROOT_USERNAME}', pwd: '${MONGO_NON_ROOT_PASSWORD}', roles:[{role:'dbOwner', db: '${MONGODB_DATABASE}'}]});"
echo '##MONGODB init script: inserting default admin user'
mongo ${MONGODB_DATABASE} \
        --host localhost \
        --port 27017 \
        -u ${MONGO_INITDB_ROOT_USERNAME} \
        -p ${MONGO_INITDB_ROOT_PASSWORD} \
        --authenticationDatabase admin \
        --eval "var defaultAdminUser = { 'username':'cloudsyncgod','password':'\$6\$rounds=656000\$CxPwYVz4B/UhdhUb\$.L9KwcTEvk6V1h7.bTbShNdND7d7XqpR2CzFecOu/Jt.YetT/nO24LCjhtH3fEb3MffUFVAIRDATaEXGGUfAT.','first_name':'CloudSync','last_name':'God','email':'cloudsync.god@heaven.org','account_closed':false,'date_created':'2021-10-21T23:33:14.921956','date_updated': null }; db.adminusers.insert(defaultAdminUser);"
