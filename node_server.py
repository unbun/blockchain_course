# Import all the packages you need
#   sha256: this is the hashing function used to create the fingerprint of the data within the block
#   json: this is a file format that will be used to store the data
#   time: this is used to generate timestamps
from hashlib import sha256
import json
import time

# Import packages for setting up an http server that allows us to visualize and add to the blockchain
from flask import Flask, request
import requests


class Block:
    def __init__(self):
        ## TO DO ##

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """

        # This takes all of the information stored in the attributes of the instance of the block class
        # and creates a JSON string from that information
        block_string = json.dumps(self.__dict__, sort_keys=True)

        # This takes the JSON string containaing all the information about the block and creates the
        # finger print of the data using the sha256 hash function
        return sha256(block_string.encode()).hexdigest()


class Blockchain:

    def __init__(self):
        ## TO DO ##

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """

        # This creates an instance of the block class where the index is 0, there are no transactions,
        # the timestamp is the current time, and previous hash is "0"
        genesis_block = Block(0, [], time.time(), "0")

        # This assigns the fingerprint of the genesis block of the chain to be the fingerprint of the
        # block instance defined in the line above
        genesis_block.hash = genesis_block.compute_hash()

        # This adds the instance of the block created to the end of the list of blocks in the blockchain
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        # This returns the last item added to the list stored in the blockchain "chain" attribute
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """

        # This gets the hash of the last block added to the chain and stores it as a local variable
        previous_hash = self.last_block.hash

        # This checks to see if the hash of the last block added to the chain matches the previous
        # hash attribute of the block that is being added. If they dod not match the block cannot
        # be added to the chain as it is not a valid part of the chain
        if previous_hash != block.previous_hash:
            return False

        # This checks to make sure that the block fingerprint matches the proof sent and that the
        # proof fingerprint starts with the number of zeroes required by the difficulty specified
        # in the chain variables. If either of these are not true the block will not be added to
        # the chain as it is not a valid part of the chain
        if not Blockchain.is_valid_proof(block, proof):
            return False

        # This assigns the hash attribute of the new block to the proof computed
        block.hash = proof
        # This adds the instance of the block to the end of the list of blocks in the chain
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """

        # This sets our first guess at the nonce as 0
        block.nonce = 0

        # This computes the block fingerprint with a nonce of 0
        computed_hash = block.compute_hash()
        # This continues to try to solve for the appropriate nonce while the hash still does not meet
        # the difficulty criteria (the hash does not start with correct number of zeroes)
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            # TO DO

        # This returns the fingerprint of the data once the difficulty criteria is met
        return computed_hash

    def add_new_transaction(self, transaction):
        # This adds the transaction to be added to the end of the list of the uncofirmed transactions
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        # This checks to make sure the hash passed starts with the number of zeroes specified by
        # the difficulty associated with the chain
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                # This checks to make sure the hash passed matches the fingerprint of the block passed
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        # This iterates through every block in the chain and recomputes the fingerprint of the block
        # and checks if the hash is valid in terms of the difficulty. If a block is found where the
        # hash is not valid then the validity is returned as False, otherwise it is True
        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """

        # This exits from the function if the list of unconfirmed transactions is empty
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        # This creates a new block where the transactions in the block are all of the unconfirmed transactions
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        # This calculates the nonce and the new fingerprint of the block that satisfies the difficulty specified
        proof = self.proof_of_work(new_block)
        # This adds the new block created to the chain after passing the appropriate checks
        self.add_block(new_block, proof)

        # This resets the unconfirmed transactions list to be empty
        self.unconfirmed_transactions = []
        # announce it to the network
        announce_new_block(new_block)
        return new_block.index


app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()

# the address to other participating members of the network
peers = set()


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    # make sure we've the longest chain
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp",
                  block_data["previous_hash"]])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    """
    Our simple consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "http://{}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


app.run(debug=True, port=8000)
