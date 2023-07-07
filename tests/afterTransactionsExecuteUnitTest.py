import math
ROUND_LENGTH = 103
ADDRESS_LENGTH = 20
NUMBER_ACTIVE_VALIDATORS = 101
WEIGHT_SCALE_FACTOR = 1000

SnapshotState = list[tuple[bytes, int]]

def getActiveValidators(validatorsTwoRoundsAgo: list[EligibleValidatorObject], roundNumber: uint32) -> list[ValidatorObject]:
    initRounds = genesisDataStore.initRounds
    initValidators = genesisDataStore.initValidators

    # During the first NUMBER_ACTIVE_VALIDATORS rounds after the bootstrap period
    # the initial validators are only partly replaced by elected validators.
    # During this phase, there are no selected standby validators.
    if roundNumber < initRounds + NUMBER_ACTIVE_VALIDATORS:
        nbrInitValidators = initRounds + NUMBER_ACTIVE_VALIDATORS - roundNumber
        nbrElectedValidators = NUMBER_ACTIVE_VALIDATORS - nbrInitValidators

        # Recall that validatorsTwoRoundsAgo is sorted by validator weight.
        electedValidatorAddresses = [item.address for item in validatorsTwoRoundsAgo[:nbrElectedValidators]]
        chosenInitValidators = [address for address in initValidators if address not in electedValidatorAddresses][:nbrInitValidators]   

        # Determine active validators and their BFT weight.
        activeValidators = [{"address": item.address, "bftWeight": math.ceil(item.weight / WEIGHT_SCALE_FACTOR) } for item in validatorsTwoRoundsAgo[:nbrElectedValidators]]
        averageElectedValidatorBftWeight = sum([item.bftWeight for item in activeValidators]) // nbrElectedValidators
        activeValidators+= [{"address": item, "bftWeight": averageElectedValidatorBftWeight} for item in chosenInitValidators]
    else:
        # If validatorsTwoRoundsAgo contains less than NUMBER_ACTIVE_VALIDATORS entries
        # there will be less than NUMBER_ACTIVE_VALIDATORS active validators.
        # Recall that validatorsTwoRoundsAgo is sorted by validator weight.
        activeValidators = [{"address": item.address, "bftWeight": math.ceil(item.weight / WEIGHT_SCALE_FACTOR) } for item in validatorsTwoRoundsAgo[:NUMBER_ACTIVE_VALIDATORS]]

    # Apply capping in weights if necessary.
    if len(activeValidators) >= ceiling(10000, MAX_BFT_WEIGHT_CAP):
        activeValidators = capWeights(activeValidators, MAX_BFT_WEIGHT_CAP)

    return activeValidators

def afterTransactionsExecuteUnitTest(height: int, initRounds: int, snapshotStore: dict[int, SnapshotState], eligibleValidators: list[dict]) -> None:
    # snapshot store at (roundNumber-2)
    
    assert height%ROUND_LENGTH == 0
    roundNumber = math.ceil(height/ROUND_LENGTH)

    # # Punished validators are excluded from the snapshot.
    # eligibleValidators = [
    #     {"address": key[-ADDRESS_LENGTH:], "weight": int.from_bytes(key[:-ADDRESS_LENGTH], 'big')}
    #     for key a substore key of the eligible validators substore if
    #     height >=  eligibleValidatorsStore(key) + PUNISHMENT_WINDOW_SELF_STAKING or
    #     eligibleValidatorsStore(key) == 0
    # ] ordered by weight, ties broken by reverse lexicographical ordering of address
    # # Notice that the keys in the substore naturally have the right ordering
    # # when being read from the end to the beginning of the store.

    snapshotStore[roundNumber] = eligibleValidators

    # Updates to Validators and BFT weights are only done after the bootstrap period.
    if roundNumber <= initRounds:
        return

    # Calculate the active validators based on the snapshot taken two rounds ago.
    validatorsTwoRoundsAgo = [item for item in snapshotStore[roundNumber - 2]]
    validatorList = getActiveValidators(validatorsTwoRoundsAgo, roundNumber)

    # If there are no eligible validators, validatorList is empty.
    # In this case, the BFT parameters and validator list are not updated.
    if validatorList == []:
        return

    # Compute the thresholds for the BFT consensus protocol.
    aggregateBFTWeight = 0
    for validator in validatorList:
        aggregateBFTWeight += validator.bftWeight

    precommitThreshold = (2 * aggregateBFTWeight) // 3 + 1
    certificateThreshold = precommitThreshold

    # Skip shuffling for simplicity
    return validatorList, snapshotStore




def afterTransactionsExecute(b: Block) -> None:
    height = b.header.height

    if isEndOfRound(height) == False:
        return

    roundNumber = roundNumber(height)


    # Bootstrap phase
    # Updates to Validators and BFT weights are only done after the bootstrap period.
    if roundNumber <= genesisDataStore.initRounds:
        return


    # Punished validators are excluded from the snapshot.
    eligibleValidators = [
        {"address": key[-ADDRESS_LENGTH:], "weight": int.from_bytes(key[:-ADDRESS_LENGTH], 'big')}
        for key a substore key of the eligible validators substore if
        height >=  eligibleValidatorsStore(key) + PUNISHMENT_WINDOW_SELF_STAKING or
        eligibleValidatorsStore(key) == 0
    ] ordered by weight, ties broken by reverse lexicographical ordering of address
    # Notice that the keys in the substore naturally have the right ordering
    # when being read from the end to the beginning of the store.

    snapshotState = {"validatorWeightSnapshot": eligibleValidators}
    create an entry in the snapshot substore with
        storeKey = roundNumber.to_bytes(4,'big'),
        storeValue = encode(snapshotStoreSchema, snapshotState)
    delete any entries from the snapshot substore snapshotStore(x) for x <= roundNumber-3


    # Hybrid phase
    if roundNumber <= initRounds + NUMBER_ACTIVE_VALIDATORS:


    # PoS phase
    elif roundNumber > initRounds + NUMBER_ACTIVE_VALIDATORS:


        # I propose to run the missed blocks logic only in the PoS phase
        

    

    # Block b is an end-of-round block. Need to update snapshot and select validators for next round.
    # This must be done after the properties related to missed blocks are updated.



    

    # Calculate the active validators based on the snapshot taken two rounds ago.
    validatorsTwoRoundsAgo = [item for item in snapshotStore(roundNumber-2)]
    validatorList = getActiveValidators(validatorsTwoRoundsAgo, roundNumber)

    # Select standby validators if relevant.
    if roundNumber > initRounds + NUMBER_ACTIVE_VALIDATORS:
        standbyValidators = [validator for validator in validatorsTwoRoundsAgo
                            if validator["address"] not in validatorList]

        selectedStandbyValidators = getSelectedStandbyValidators(standbyValidators, height)
        # Add selected standby validators to validators.
        validatorList += selectedStandbyValidators

    # If there are no eligible validators, validatorList is empty.
    # In this case, the BFT parameters and validator list are not updated.
    if validatorList == []:
        return

    shuffleAndSetValidators(validatorList)

def updateMissedBlocks(b: Block) -> None:
    height = b.header.height
    # previousTimestamp is the value in the previous timestamp substore.
    missedBlocks = Validators.getGeneratorsBetweenTimestamps(previousTimestamp, b.header.timestamp)

    for address in missedBlocks:
        validatorStore(address).consecutiveMissedBlocks += missedBlocks[address]

        # The below rule was introduced in LIP 0023.
        if (validatorStore(address).consecutiveMissedBlocks > FAIL_SAFE_MISSED_BLOCKS
            and height - validatorStore(address).lastGeneratedHeight > FAIL_SAFE_INACTIVE_WINDOW):
            validatorStore(address).isBanned = True
            updateValidatorEligibility(address,getValidatorWeight(address))

    validatorStore(b.header.generatorAddress).consecutiveMissedBlocks = 0
    validatorStore(b.header.generatorAddress).lastGeneratedHeight = height

    # Update previousTimestamp substore.
    previousTimestamp = b.header.timestamp

def shuffleAndSetValidators(validatorList) -> None:
    # Compute the thresholds for the BFT consensus protocol.
    aggregateBFTWeight = 0
    for validator in validatorList:
        aggregateBFTWeight += validator.bftWeight

    precommitThreshold = (2 * aggregateBFTWeight) // 3 + 1
    certificateThreshold = precommitThreshold

    # Random seed to shuffle validators.
    randomSeed = random.getRandomBytes(
        height +1 - (ROUND_LENGTH*3)//2,
        ROUND_LENGTH
    )
    shuffledValidatorList = shuffleValidatorsList(validatorList, randomSeed)

    Validators.setValidatorParams(precommitThreshold, certificateThreshold, shuffledValidatorList)