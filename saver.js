const driver = require('bigchaindb-driver')
const base58 = require('bs58');
var awsIot = require('aws-iot-device-sdk');
const { Ed25519Sha256 } = require('crypto-conditions');


const owner = new driver.Ed25519Keypair()

const API_PATH = 'https://test.ipdb.io/api/v1/'
const conn = new driver.Connection(API_PATH)

registeredDevices = {}

function registerThermo(id) {
    
    const txCreate = driver.Transaction.makeCreateTransaction(
        {
           'id': id
        },
        {
            event: 'registration',
            datetime: new Date().toString(),
        },
        [driver.Transaction.makeOutput(
            driver.Transaction.makeEd25519Condition(owner.publicKey))],
        owner.publicKey
    )
    const txSigned = driver.Transaction.signTransaction(txCreate,
        owner.privateKey)
    conn.postTransactionCommit(txSigned)
        .then(res => {
            registeredDevices[id] = txSigned.id;
            console.log(registeredDevices);
            
        })
}

function registerTemp(txCreatedID, newTemp, id) {
    conn.getTransaction(txCreatedID)
        .then((txCreated) => {
            console.log(txCreated);
            const createTranfer = driver.Transaction.
            makeTransferTransaction(
                // The output index 0 is the one that is being spent
                [{
                    tx: txCreated,
                    output_index: 0
                }],
                [driver.Transaction.makeOutput(
                    driver.Transaction.makeEd25519Condition(
                        owner.publicKey))],
                {
                    event: 'temperature',
                    value: newTemp,
                    datetime: new Date().toString(),
                }
            )
        
            const signedTransfer = driver.Transaction
                .signTransaction(createTranfer, owner.privateKey)
            return conn.postTransactionCommit(signedTransfer)
        })
        .then(res => {
            console.log(res);
            registeredDevices[id] = res.id;
        })
}


var device = awsIot.device({
    keyPath: "certificates/9edb23887d-private.pem.key",
   certPath: "certificates/9edb23887d-certificate.pem.crt",
     caPath: "certificates/root.pem",
   clientId:  "testDevice",
       host: "a24ojhzjcj6a8j-ats.iot.us-east-1.amazonaws.com"
 });

 device
  .on('connect', function() {
    console.log('connect');
    device.subscribe('/devices/thermostats/+/get_ambient_temperature_return');
    device.subscribe('/devices/info');
  });

  device
  .on('message', function(topic, payload) {
      if(topic=='/devices/info'){
          console.log( parseInt(payload.toString().substring(11,13)))
          registerThermo( parseInt(payload.toString().substring(11,13)))
      }
      if(topic.match(new RegExp('\/devices\/thermostats\/[0-9]+\/get_ambient_temperature_return'))!=null){
        console.log("id:" + topic.match('[0-9]+')[0]);
        let id = parseInt(topic.match('[0-9]+')[0])
        registerTemp(registeredDevices[id],parseFloat(payload.toString().match('[0-9.]+')[0]),id)
      }
  });

