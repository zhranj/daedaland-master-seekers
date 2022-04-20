import pytest
import brownie
from brownie import accounts, MockNft
from scripts.utilities import get_deployer_account, get_user_account


INDEX_PRICE = 0
INDEX_PREREQUISITE = 1
INDEX_UNLOCKS = 2
INDEX_ACTIVATIONS = 3
INDEX_NAME = 4
INDEX_BASEURI = 5
INDEX_ENABLED = 6
INDEX_AVAILABLE = 7
INDEX_AUTO_UNLOCK = 8


def add_and_unlock_generation(contract, user, cost=0, prereq=0, token_id=0, skip_unlock=False):
    new_id = contract.getGenerationCount()
    contract.addGeneration("Test", "", cost, prereq, cost==0)
    contract.enableGeneration(new_id)
    if cost > 0:
        contract.setGenerationAvailability(new_id, True)
        if token_id > 0 and not skip_unlock:
            contract.unlockGeneration(token_id, new_id, {"from": user, "value": cost})


@pytest.fixture(scope="function", autouse=True)
def user():
    return get_user_account()


@pytest.fixture(scope="function", autouse=True)
def deployer():
    return get_deployer_account()


def test_deploy_mimetic(deployer):
    MockNft.deploy({"from": deployer})
    contract = MockNft[-1]
    assert contract is not None


@pytest.fixture(scope="function", autouse=True)
def mimetic(deployer):
    MockNft.deploy({"from": deployer})
    skrs = MockNft[-1]
    skrs.enableGeneration(0)
    yield skrs


def test_initial_layer_created_when_contract_deployed(mimetic):
    assert mimetic.getGenerationCount() == 1


def test_add_generation_fails_when_invalid_name(mimetic):
    with brownie.reverts("MimeticERC721: Invalid generation name"):
        mimetic.addGeneration("", "baseURI", 14, 0, False)


def test_add_generation_fails_autounlock_with_price(mimetic):
    with brownie.reverts("MimeticERC721: Auto-unlock generation must have no associated price"):
        mimetic.addGeneration("Test", "baseURI", 14, 0, True)


def test_add_generation_fails_prerequsitie_nonexistent(mimetic):
    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.addGeneration("Test", "baseURI", 1337, 2, False)


def test_add_generation_fails_auto_unlock_prerequisite_auto_unlock(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.addGeneration("Test", "baseURI", 0, 1, True)


def test_add_generation_fails_auto_unlock_prerequisite_self(mimetic):
    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.addGeneration("Test", "baseURI", 0, 1, True)


def test_add_generation_fails_when_first_generation_auto_unlock(mimetic):
    mimetic.disableGeneration(0)
    mimetic.removeGeneration(0)

    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.addGeneration("Test", "baseURI", 0, 0, True)


def test_add_generation_succeds_prereq_enabled_and_different(mimetic):
    gen_count_before = mimetic.getGenerationCount()

    mimetic.addGeneration("Test", "baseURI", 1337, 0, False)

    assert mimetic.getGenerationCount() == gen_count_before + 1


def test_add_generation_succeds_no_prereq(mimetic):
    gen_count_before = mimetic.getGenerationCount()

    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    assert mimetic.getGenerationCount() == gen_count_before + 1


def test_add_generation_fails_when_not_owner(mimetic, user):
    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.addGeneration("Test", "baseURI", 0, 0, True, {"from": user})


def test_remove_generation_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.removeGeneration(1, {"from": user})


def test_remove_generation_fails_when_generation_enabled(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    with brownie.reverts("MimeticERC721: Generation must be disabled"):
        mimetic.removeGeneration(1)


def test_remove_generation_fails_when_not_latest(mimetic, user):
    mimetic.addGeneration("Test 1", "baseURI", 0, 0, True)
    mimetic.addGeneration("Test 2", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Only the most recently added generation may be removed"):
        mimetic.removeGeneration(1)


def test_remove_generation_succeeds(mimetic, user):
    mimetic.addGeneration("Test 1", "baseURI", 0, 0, True)
    mimetic.addGeneration("Test 2", "baseURI", 0, 0, True)
    gen_count_before = mimetic.getGenerationCount()

    mimetic.removeGeneration(2)

    assert mimetic.getGenerationCount() == gen_count_before - 1


def test_set_generation_name_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.setGenerationName(1, "Cool Name", {"from": user})


def test_set_generation_name_fails_when_enabled(mimetic):
    with brownie.reverts("MimeticERC721: Generation must be disabled"):
        mimetic.setGenerationName(0, "Cool Name")


def test_set_generation_name_fails_when_empty(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Invalid generation name"):
        mimetic.setGenerationName(1, "")


def test_set_generation_name_succeeds(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    mimetic.setGenerationName(1, "Cool Name")

    assert mimetic.generations(1)[INDEX_NAME] == "Cool Name"


def test_set_generation_baseURI_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.setGenerationBaseUri(1, "ipfs://Cool", {"from": user})


def test_set_generation_baseURI_fails_when_empty(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Invalid base URI"):
        mimetic.setGenerationBaseUri(1, "")


def test_set_generation_baseURI_succeeds_disabled(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    mimetic.setGenerationBaseUri(1, "ipfs://Cool")

    assert mimetic.generations(1)[INDEX_BASEURI] == "ipfs://Cool"


def test_set_generation_baseURI_succeeds_enabled(mimetic):
    mimetic.setGenerationBaseUri(0, "ipfs://Cool")

    assert mimetic.generations(0)[INDEX_BASEURI] == "ipfs://Cool"


def test_set_generation_price_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.setGenerationPrice(1, 1337, {"from": user})


def test_set_generation_price_fails_when_enabled(mimetic):
    with brownie.reverts("MimeticERC721: Generation must be disabled"):
        mimetic.setGenerationPrice(0, 1337)


def test_set_generation_price_fails_when_autounlock(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Auto-unlock must be free"):
        mimetic.setGenerationPrice(1, 1337)


def test_set_generation_price_succeeds(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    mimetic.setGenerationPrice(1, 1337)

    assert mimetic.generations(1)[INDEX_PRICE] == 1337


def test_set_generation_prerequisite_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.setGenerationPrerequisite(1, 0, {"from": user})


def test_set_generation_prerequisite_fails_when_enabled(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)
    mimetic.enableGeneration(1)

    with brownie.reverts("MimeticERC721: Generation must be disabled"):
        mimetic.setGenerationPrerequisite(1, 0)


def test_set_generation_prerequisite_fails_when_prerequsite_invalid(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.setGenerationPrerequisite(1, 2)


def test_set_generation_prerequisite_fails_when_prereq_auto_unlock(mimetic):
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    mimetic.addGeneration("Test", "baseURI", 42, 2, False)

    with brownie.reverts("MimeticERC721: Invalid prerequisite generation"):
        mimetic.setGenerationPrerequisite(2, 1)


def test_set_generation_prerequisite_succeeds_when_prereq_enabled(mimetic):
    mimetic.addGeneration("A", "baseURI", 42, 0, False)
    mimetic.addGeneration("B", "baseURI", 0, 1, True)

    mimetic.setGenerationPrerequisite(2, 0)

    assert mimetic.generations(1)[INDEX_PREREQUISITE] == 0


def test_set_generation_prerequisite_succeeds_when_prereq_disabled(mimetic):
    mimetic.addGeneration("A", "baseURI", 42, 0, False)
    mimetic.addGeneration("B", "baseURI", 0, 1, True)
    mimetic.disableGeneration(0)

    mimetic.setGenerationPrerequisite(1, 0)

    assert mimetic.generations(1)[INDEX_PREREQUISITE] == 0


def test_set_generation_availability_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.setGenerationAvailability(1, True, {"from": user})


def test_set_generation_availability_fails_when_invalid_generation(mimetic):
    with brownie.reverts("MimeticERC721: Invalid generation"):
        mimetic.setGenerationAvailability(42, True)


def test_set_generation_availability_succeeds(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    mimetic.setGenerationAvailability(1, True)

    assert mimetic.generations(1)[INDEX_AVAILABLE]


def test_enable_generation_fails_when_not_owner(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.enableGeneration(1, {"from": user})


def test_enable_generation_fails_when_already_enabled(mimetic):
    with brownie.reverts("MimeticERC721: Generation must be disabled"):
        mimetic.enableGeneration(0)


def test_enable_generation_fails_when_prereq_disabled(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.disableGeneration(0)

    with brownie.reverts("MimeticERC721: Prerequisite must be enabled"):
        mimetic.enableGeneration(1)


def test_enable_generation_succeeds_when_baseURI_empty(mimetic):
    mimetic.addGeneration("Test", "", 42, 0, False)

    assert not mimetic.generations(1)[INDEX_ENABLED]

    mimetic.enableGeneration(1)

    assert mimetic.generations(1)[INDEX_ENABLED]


def test_enable_generation_succeeds_no_prereq(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 1, False)

    assert not mimetic.generations(1)[INDEX_ENABLED]

    mimetic.enableGeneration(1)

    assert mimetic.generations(1)[INDEX_ENABLED]


def test_enable_generation_succeeds_with_prereq(mimetic):
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)

    assert not mimetic.generations(1)[INDEX_ENABLED]

    mimetic.enableGeneration(1)

    assert mimetic.generations(1)[INDEX_ENABLED]


def test_disable_generation_fails_when_not_owner(mimetic, user):
    with brownie.reverts("Ownable: caller is not the owner"):
        mimetic.disableGeneration(0, {"from": user})


def test_disable_generation_fails_when_already_disabled(mimetic, user):
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)

    with brownie.reverts("MimeticERC721: Generation must be enabled"):
        mimetic.disableGeneration(1)


def test_disable_generation_fails_autounlock_with_activations(mimetic, user):
    mimetic.mint(1, {"from": user})

    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)
    mimetic.activateGeneration(1, 1, {"from": user})

    with brownie.reverts("MimeticERC721: Generation is actively used"):
        mimetic.disableGeneration(1)


def test_disable_generation_fails_unlockable_with_unlocks(mimetic, user):
    mimetic.mint(1, {"from": user})

    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    mimetic.unlockGeneration(1, 1, {"from": user, "value": 42})

    with brownie.reverts("MimeticERC721: Generation already has unlocks"):
        mimetic.disableGeneration(1)


def test_disable_generation_succeeds_autounlock_without_activations(mimetic, user):
    mimetic.mint(1, {"from": user})

    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    mimetic.disableGeneration(1)

    assert not mimetic.generations(1)[INDEX_ENABLED]


def test_disable_generation_succeeds_unlockable_without_unlocks(mimetic, user):
    mimetic.mint(1, {"from": user})

    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    mimetic.disableGeneration(1)

    assert not mimetic.generations(1)[INDEX_ENABLED]


def test_unlock_generation_fails_when_generation_disabled(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)

    with brownie.reverts("MimeticERC721: Generation must be enabled"):
        mimetic.unlockGeneration(99, 1, {"from": user, "value": 42})


def test_unlock_generation_fails_when_generation_not_available(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)

    with brownie.reverts("MimeticERC721: Generation unavailable"):
        mimetic.unlockGeneration(99, 1, {"from": user, "value": 42})


def test_unlock_generation_fails_when_already_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=0, token_id=99)

    with brownie.reverts("MimeticERC721: Generation already unlocked"):
        mimetic.unlockGeneration(99, 1, {"from": user, "value": 42})


def test_unlock_generation_fails_when_generation_auto_unlock(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    with brownie.reverts("MimeticERC721: Generation already unlocked"):
        mimetic.unlockGeneration(99, 1, {"from": user, "value": 0})


def test_unlock_generation_fails_when_insufficient_funds(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    with brownie.reverts("MimeticERC721: Insufficient funds"):
        mimetic.unlockGeneration(99, 1, {"from": user, "value": 41})


def test_unlock_generation_fails_when_generation_invalid(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    with brownie.reverts("MimeticERC721: Generation must be enabled"):
        mimetic.unlockGeneration(99, 2, {"from": user, "value": 42})


def test_unlock_generation_fails_when_prerequisite_locked(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)
    mimetic.addGeneration("Test 2", "baseURI2", 43, 1, False)
    mimetic.enableGeneration(2)
    mimetic.setGenerationAvailability(2, True)

    with brownie.reverts("MimeticERC721: Must unlock prerequisite generation first"):
        mimetic.unlockGeneration(99, 2, {"from": user, "value": 43})


def test_unlock_generation_succeeds_when_no_prereq(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.isGenerationUnlocked(99, 1)


def test_unlock_generation_succeeds_when_prereq_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=0, token_id=99)
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.isGenerationUnlocked(99, 2)


def test_unlock_generation_succeeds_when_done_from_alt_wallet(mimetic, user, deployer):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    mimetic.unlockGeneration(99, 1, {"from": deployer, "value": 43})

    assert mimetic.isGenerationUnlocked(99, 1)


def test_unlock_generation_updates_unlocks_counter(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    mimetic.addGeneration("Test 2", "baseURI2", 43, 0, False)
    mimetic.enableGeneration(2)
    mimetic.setGenerationAvailability(2, True)

    unlocks_before = mimetic.generations(2)[INDEX_UNLOCKS]
    mimetic.unlockGeneration(99, 2, {"from": user, "value": 43})

    assert mimetic.generations(2)[INDEX_UNLOCKS] == unlocks_before + 1


def test_activate_generation_fails_when_generation_disabled(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)

    with brownie.reverts("MimeticERC721: Generation must be enabled"):
        mimetic.activateGeneration(99, 1, {"from": user})


def test_activate_generation_fails_when_not_token_owner(mimetic, user, deployer):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    with brownie.reverts("MimeticERC721: Must be token owner"):
        mimetic.activateGeneration(99, 1, {"from": deployer})


def test_activate_generation_fails_when_not_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    with brownie.reverts("MimeticERC721: Must unlock first"):
        mimetic.activateGeneration(99, 1, {"from": user})


def test_activate_generation_fails_when_prereq_not_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 42, 0, False)
    mimetic.enableGeneration(1)
    mimetic.setGenerationAvailability(1, True)

    mimetic.addGeneration("Test 2", "baseURI2", 0, 1, True)
    mimetic.enableGeneration(2)

    with brownie.reverts("MimeticERC721: Must unlock prerequisite generation first"):
        mimetic.activateGeneration(99, 2, {"from": user})


def test_activate_generation_succeeds_when_auto_unlock(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.addGeneration("Test", "baseURI", 0, 0, True)
    mimetic.enableGeneration(1)

    assert mimetic.tokenToGenerationId(99) == 0

    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.tokenToGenerationId(99) == 1


def test_activate_generation_succeeds_when_no_prereq(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.tokenToGenerationId(99) == 0

    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.tokenToGenerationId(99) == 1


def test_activate_generation_succeeds_when_auto_and_prereq_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=0, token_id=99)

    mimetic.addGeneration("Test 2", "baseURI2", 0, 1, True)
    mimetic.enableGeneration(2)

    assert mimetic.tokenToGenerationId(99) == 0

    mimetic.activateGeneration(99, 2, {"from": user})

    assert mimetic.tokenToGenerationId(99) == 2


def test_activate_generation_succeeds_when_unlockable_and_prereq_unlocked(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=0, token_id=99)
    add_and_unlock_generation(mimetic, user, cost=43, prereq=1, token_id=99)

    assert mimetic.tokenToGenerationId(99) == 0

    mimetic.activateGeneration(99, 2, {"from": user})

    assert mimetic.tokenToGenerationId(99) == 2


def test_activate_generation_decrements_previous_generation_activations(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.tokenToGenerationId(99) == 0
    prev_gen_activations = mimetic.generations(0)[INDEX_ACTIVATIONS]

    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == prev_gen_activations - 1


def test_activate_generation_increments_new_generation_activations(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.tokenToGenerationId(99) == 0
    next_gen_activations = mimetic.generations(1)[INDEX_ACTIVATIONS]

    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.generations(1)[INDEX_ACTIVATIONS] == next_gen_activations + 1


def test_generation_baseuri_returns_default_generation_baseuri_when_revealed(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)

    assert mimetic.generationBaseURI(99) == mimetic.generations(0)[INDEX_BASEURI]


def test_generation_baseuri_returns_unrevealed_baseuri_when_unrevealed(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)
    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.generationBaseURI(99) == mimetic.baseURI()


def test_generation_baseuri_returns_correct_baseuri_after_reveal(mimetic, user):
    mimetic.mint(99, {"from": user})
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)
    mimetic.activateGeneration(99, 1, {"from": user})

    mimetic.setGenerationBaseUri(1, "ipfs://Cool")

    assert mimetic.generationBaseURI(99) == mimetic.generations(1)[INDEX_BASEURI]


def test_generation_baseuri_returns_correct_baseuri_genesis_generation(mimetic, user):
    mimetic.setGenerationBaseUri(0, "ipfs://Cooluri")
    mimetic.mint(99, {"from": user})

    assert mimetic.generationBaseURI(99) == mimetic.generations(0)[INDEX_BASEURI]


def test_generation_baseuri_returns_correct_baseuri_genesis_generation_simulation(mimetic, user):
    mimetic.mint(99, {"from": user})

    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)
    mimetic.activateGeneration(99, 1, {"from": user})

    assert mimetic.generationBaseURI(99) == mimetic.baseURI()

    mimetic.setGenerationBaseUri(1, "ipfs://Cooluri")

    assert mimetic.generationBaseURI(99) == mimetic.generations(1)[INDEX_BASEURI]


def test_mint_increments_unlocks(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.mint(101, {"from": user})

    state_before = mimetic.generations(0)[INDEX_UNLOCKS]

    mimetic.mint(191, {"from": user})

    assert mimetic.generations(0)[INDEX_UNLOCKS] == state_before + 1


def test_mint_increments_activations(mimetic, user):
    mimetic.mint(99, {"from": user})
    mimetic.mint(101, {"from": user})

    state_before = mimetic.generations(0)[INDEX_ACTIVATIONS]

    mimetic.mint(191, {"from": user})

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == state_before + 1


def test_mint_sets_active_generation_to_zero(mimetic, user):
    mimetic.mint(191, {"from": user})

    assert mimetic.tokenToGenerationId(191) == 0


def test_mint_sets_unlocked_generations_to_gen_zero(mimetic, user):
    mimetic.mint(191, {"from": user})

    assert mimetic.tokenToUnlockedGenerations(191) == (1 << 0)


def test_burn_decrements_all_unlocked_generations(mimetic, user):
    mimetic.mint(99, {"from": user})

    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)  # gen = 1
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)  # gen = 2
    add_and_unlock_generation(mimetic, user, cost=0, prereq=2, token_id=99)  # gen = 3
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99, skip_unlock=True)  # gen = 4

    assert mimetic.generations(0)[INDEX_UNLOCKS] == 1
    assert mimetic.generations(1)[INDEX_UNLOCKS] == 1
    assert mimetic.generations(2)[INDEX_UNLOCKS] == 1
    assert mimetic.generations(3)[INDEX_UNLOCKS] == 0
    assert mimetic.generations(4)[INDEX_UNLOCKS] == 0

    mimetic.burn(99)

    assert mimetic.generations(0)[INDEX_UNLOCKS] == 0
    assert mimetic.generations(1)[INDEX_UNLOCKS] == 0
    assert mimetic.generations(2)[INDEX_UNLOCKS] == 0
    assert mimetic.generations(3)[INDEX_UNLOCKS] == 0
    assert mimetic.generations(4)[INDEX_UNLOCKS] == 0  # this one was 0 before burn too


def test_burn_decrements_active_generation_default(mimetic, user):
    mimetic.mint(99, {"from": user})

    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)  # gen = 1
    add_and_unlock_generation(mimetic, user, cost=0, prereq=1, token_id=99)  # gen = 2
    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99, skip_unlock=True)  # gen = 3

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == 1
    assert mimetic.generations(1)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(2)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(3)[INDEX_ACTIVATIONS] == 0

    mimetic.burn(99)

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(1)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(2)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(3)[INDEX_ACTIVATIONS] == 0


def test_burn_decrements_active_generation_custom(mimetic, user):
    mimetic.mint(99, {"from": user})

    add_and_unlock_generation(mimetic, user, cost=42, prereq=1, token_id=99)  # gen = 1
    add_and_unlock_generation(mimetic, user, cost=0, prereq=1, token_id=99)  # gen = 2

    mimetic.activateGeneration(99, 2, {"from": user})

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(1)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(2)[INDEX_ACTIVATIONS] == 1

    mimetic.burn(99)

    assert mimetic.generations(0)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(1)[INDEX_ACTIVATIONS] == 0
    assert mimetic.generations(2)[INDEX_ACTIVATIONS] == 0

