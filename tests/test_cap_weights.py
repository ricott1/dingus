import os
from typing import TypedDict

class ValidatorObject(TypedDict):
    address: bytes
    bftWeight: int

def ceiling(x: int,y: int) -> int:
    if y == 0:
        raise Exception('Can not divide by 0.')
    return (x+y-1)//y

def capWeights(validatorList: list[ValidatorObject], capValue: int) -> list[ValidatorObject]:
    """Cap the weights of the validators in the list.
    
    Args:
        validatorList (list[ValidatorObject]): List of validators.
        capValue (int): Value to cap the weights. Specifies the percentage in which the values are capped. 
                        Takes values from 0 - 10000 corresponding to double decimal precision integers 
                        which can be obtained by dividing it by 100, i.e., 1000 means 10%.
    """

    
    if sorted(validatorList, reverse = True, key = lambda y:y["bftWeight"]) != validatorList: # List should be ordered in decreasing order of weight.
        raise Exception('List is not sorted in decreasing order.')
    if capValue == 0 or capValue >= 10000:
        raise Exception('Invalid value for capping.')

    maxNumCappedElements = ceiling(10000, capValue) - 1
    if len(validatorList) <= maxNumCappedElements:
        raise Exception('List size not enough to apply capping with specified value.')

    partialSum = 0
    for i in range(maxNumCappedElements + 1, len(validatorList)):
        partialSum += validatorList[i]["bftWeight"]

    for i in range(maxNumCappedElements, 0, -1):
       partialSum += validatorList[i]["bftWeight"]
       cappedWeightRemainingElements = (capValue * partialSum) // (10000 - (capValue * i))
       if cappedWeightRemainingElements < validatorList[i-1]["bftWeight"]:
           for k in range(i):
              validatorList[k]["bftWeight"] = cappedWeightRemainingElements
           break

    return validatorList


test_validators = [
    {'address': os.urandom(20), 'bftWeight': 6000},
    {'address': os.urandom(20), 'bftWeight': 5500},
    {'address': os.urandom(20), 'bftWeight': 5000},
    {'address': os.urandom(20), 'bftWeight': 4000},
    {'address': os.urandom(20), 'bftWeight': 3000},
    {'address': os.urandom(20), 'bftWeight': 3000},
    {'address': os.urandom(20), 'bftWeight': 2000},
    {'address': os.urandom(20), 'bftWeight': 1000},
    {'address': os.urandom(20), 'bftWeight': 750},
]

# test_validators = sorted(test_validators_wrong_order, reverse=True, key = lambda y:y["bftWeight"])


if __name__ == "__main__":
   
    print("test_validators: ", [v["bftWeight"] for v in test_validators])
    tot_BFT_weight = sum([v["bftWeight"] for v in test_validators])
    print("Total BFT weight", tot_BFT_weight)
    
    print("BFT percentage", [f"{(v['bftWeight']*10000//tot_BFT_weight)/100}" for v in test_validators], f"= {sum([(v['bftWeight']*10000/tot_BFT_weight)/100 for v in test_validators])}")
    
    
    for cap in (1700, 1900, 2000, 2100, 2500, 3000):
        test_validators = [
            {'address': os.urandom(20), 'bftWeight': 6000},
            {'address': os.urandom(20), 'bftWeight': 5500},
            {'address': os.urandom(20), 'bftWeight': 5000},
            {'address': os.urandom(20), 'bftWeight': 4000},
            {'address': os.urandom(20), 'bftWeight': 3000},
            {'address': os.urandom(20), 'bftWeight': 3000},
            {'address': os.urandom(20), 'bftWeight': 2000},
            {'address': os.urandom(20), 'bftWeight': 1000},
            {'address': os.urandom(20), 'bftWeight': 750},
        ]
        capped_validators = capWeights(test_validators, cap)
        print(f"\nCapping at {cap/100}%")
        print("capped validators", [v["bftWeight"] for v in capped_validators])
        tot_capped_BFT_weight = sum([v["bftWeight"] for v in test_validators])
        print("capped BFT percentage", [f"{(v['bftWeight']*10000//tot_capped_BFT_weight)/100}" for v in capped_validators], f"= {sum([(v['bftWeight']*10000/tot_capped_BFT_weight)/100 for v in capped_validators])}")