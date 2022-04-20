// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

abstract contract MimeticERC721 is ERC721Enumerable, Ownable {
    using Strings for uint256;

    struct Generation {
        // Price to unlock. Once unlocked, owner may freely switch between the active generations.
        uint256 price;
        // Another generation which the user must own before they can unlock a specific generation.
        uint256 prerequisiteGeneration;
        // Number of times the specific generation was unlocked (purchased).
        uint256 unlocks;
        // Number of current activations the generation has.
        uint256 activations;
        // Name of the generation.
        string name;
        // Base URI for the generation. If not set, the `_getUnrevealedUri` is used.
        string baseUri;
        // Flag whether the generation is enabled. Only enabled generations may be unlocked or activated.
        bool enabled;
        // Flag whether the generation is available for unlocking. Can be used to facilitate offerings for limited periods of time.
        bool available;
        // Flag whether the generation is automatically unlocked if the user owns the prerequisite generation.
        bool autoUnlock;
    }

    Generation[] public generations;
    mapping(uint256 => uint256) public tokenToGenerationId;
    // bit-encoded generations (up to 256)
    mapping(uint256 => uint256) public tokenToUnlockedGenerations;

    // Events
    event GenerationAdded(uint256 indexed generationId);
    event GenerationEnabledDisabled(uint256 indexed generationId, bool isEnabled);
    event GenerationUnlocked(uint256 indexed generationId, uint256 indexed tokenId, address indexed sender);
    event GenerationActivated(uint256 indexed generationId, uint256 indexed tokenId);

    modifier whenGenerationDisabled(uint256 _generationId) {
        require(_generationId < generations.length && !generations[_generationId].enabled, "MimeticERC721: Generation must be disabled");
        _;
    }

    modifier whenGenerationEnabled(uint256 _generationId) {
        require(_generationId < generations.length && generations[_generationId].enabled, "MimeticERC721: Generation must be enabled");
        _;
    }

    modifier whenGenerationAvailable(uint256 _generationId) {
        require(_generationId < generations.length && generations[_generationId].available, "MimeticERC721: Generation unavailable");
        _;
    }

    function addGeneration(
            string memory _name,
            string memory _baseUri,
            uint256 _price,
            uint256 _prereqGeneration,
            bool _autoUnlock) public onlyOwner {
        require(bytes(_name).length > 0, "MimeticERC721: Invalid generation name");
        require(generations.length >= _prereqGeneration, "MimeticERC721: Invalid prerequisite generation");
        require(generations.length == _prereqGeneration || !generations[_prereqGeneration].autoUnlock, "MimeticERC721: Invalid prerequisite generation");
        if (_autoUnlock) {
            require(generations.length != _prereqGeneration, "MimeticERC721: Invalid prerequisite generation");
            require(_price == 0, "MimeticERC721: Auto-unlock generation must have no associated price");
        }

        emit GenerationAdded(generations.length);

        generations.push(Generation({
             name: _name
            ,enabled: false
            ,baseUri: _baseUri
            ,price: _price
            ,prerequisiteGeneration: _prereqGeneration
            ,unlocks: 0
            ,activations: 0
            ,autoUnlock: _autoUnlock
            ,available: false
        }));
    }

    function removeGeneration(uint256 _generationId)
            public
            whenGenerationDisabled(_generationId)
            onlyOwner {
        require(_generationId + 1 == generations.length, "MimeticERC721: Only the most recently added generation may be removed");
        generations.pop();
    }

    function getGenerationCount() public view returns (uint256) {
        return generations.length;
    }

    function setGenerationName(uint256 _generationId, string memory _newName)
            public
            whenGenerationDisabled(_generationId)
            onlyOwner {
        require(bytes(_newName).length > 0, "MimeticERC721: Invalid generation name");
        generations[_generationId].name = _newName;
    }

    function setGenerationBaseUri(uint256 _generationId, string memory _baseUri)
            public
            onlyOwner {
        require(bytes(_baseUri).length > 0, "MimeticERC721: Invalid base URI");
        generations[_generationId].baseUri = _baseUri;
    }

    function setGenerationPrice(uint256 _generationId, uint256 _price)
            public
            whenGenerationDisabled(_generationId)
            onlyOwner {
        require(!generations[_generationId].autoUnlock, "MimeticERC721: Auto-unlock must be free");
        generations[_generationId].price = _price;
    }

    function setGenerationPrerequisite(uint256 _generationId, uint256 _prereqGeneration)
            public
            whenGenerationDisabled(_generationId)
            onlyOwner {
        require(generations.length > _prereqGeneration, "MimeticERC721: Invalid prerequisite generation");
        require(!generations[_prereqGeneration].autoUnlock, "MimeticERC721: Invalid prerequisite generation");
        generations[_generationId].prerequisiteGeneration = _prereqGeneration;
    }

    function setGenerationAvailability(uint256 _generationId, bool _availability)
             public
             onlyOwner {
        require(_generationId < generations.length, "MimeticERC721: Invalid generation");
        generations[_generationId].available = _availability;
    }

    function enableGeneration(uint256 _generationId)
            public
            whenGenerationDisabled(_generationId)
            onlyOwner {
        uint256 prereqId = generations[_generationId].prerequisiteGeneration;
        require(_generationId == prereqId || generations[prereqId].enabled, "MimeticERC721: Prerequisite must be enabled");
        generations[_generationId].enabled = true;
        emit GenerationEnabledDisabled(_generationId, true);
    }

    function disableGeneration(uint256 _generationId)
            public
            whenGenerationEnabled(_generationId)
            onlyOwner {
        Generation storage gen = generations[_generationId];
        if (gen.autoUnlock) {
            require(gen.activations == 0, "MimeticERC721: Generation is actively used");
        } else {
            require(gen.unlocks == 0, "MimeticERC721: Generation already has unlocks");
        }

        gen.enabled = false;
        emit GenerationEnabledDisabled(_generationId, false);
    }

    function isGenerationUnlocked(uint256 _tokenId, uint256 _generationId) public view returns (bool) {
        Generation memory gen = generations[_generationId];
        if (gen.autoUnlock) {
            return isGenerationUnlocked(_tokenId, gen.prerequisiteGeneration);
        }

        uint256 unlocksForToken = tokenToUnlockedGenerations[_tokenId];
        uint256 unlockBit = 1 << _generationId;
        return unlocksForToken & unlockBit == unlockBit;
    }

    function unlockGeneration(uint256 _tokenId, uint256 _generationId)
            public
            payable
            whenGenerationEnabled(_generationId)
            whenGenerationAvailable(_generationId) {
        Generation storage gen = generations[_generationId];
        uint256 unlockBit = 1 << _generationId;
        uint256 unlocksForToken = tokenToUnlockedGenerations[_tokenId];
        require(!gen.autoUnlock && unlocksForToken & unlockBit != unlockBit, "MimeticERC721: Generation already unlocked");
        require(msg.value >= gen.price, "MimeticERC721: Insufficient funds");

        if (gen.prerequisiteGeneration != _generationId) {
            require(isGenerationUnlocked(_tokenId, gen.prerequisiteGeneration), "MimeticERC721: Must unlock prerequisite generation first");
        }

        tokenToUnlockedGenerations[_tokenId] = unlocksForToken | unlockBit;
        gen.unlocks++;

        emit GenerationUnlocked(_generationId, _tokenId, msg.sender);
    }

    function activateGeneration(uint256 _tokenId, uint256 _generationId)
            public
            whenGenerationEnabled(_generationId) {
        require(ownerOf(_tokenId) == msg.sender, "MimeticERC721: Must be token owner");
        Generation storage gen = generations[_generationId];

        if (gen.autoUnlock) {
            require(isGenerationUnlocked(_tokenId, gen.prerequisiteGeneration), "MimeticERC721: Must unlock prerequisite generation first");
        } else {
            uint256 unlockBit = 1 << _generationId;
            uint256 unlocksForToken = tokenToUnlockedGenerations[_tokenId];
            require(unlocksForToken & unlockBit == unlockBit, "MimeticERC721: Must unlock first");
        }

        generations[tokenToGenerationId[_tokenId]].activations--;
        tokenToGenerationId[_tokenId] = _generationId;
        gen.activations++;

        emit GenerationActivated(_generationId, _tokenId);
    }

    function _generationBaseURI(uint256 _tokenId) internal view virtual returns (string memory) {
        uint256 activeGenerateion = tokenToGenerationId[_tokenId];
        Generation memory gen = generations[activeGenerateion];

        // Check if revealed
        if (bytes(gen.baseUri).length > 0) {
            return gen.baseUri;
        }

        // Use ERC721._baseURI() as the unrevealed URI, since it is not applicable for anything else anyway.
        return _baseURI();
    }

    function _mint(address _to, uint256 _tokenId) internal virtual override {
        super._mint(_to, _tokenId);

        Generation storage gen = generations[0];
        gen.unlocks++;
        gen.activations++;
        tokenToGenerationId[_tokenId] = 0;
        tokenToUnlockedGenerations[_tokenId] = 1;  // 1 << 0
    }

    function _burn(uint256 _tokenId) internal virtual override {
        uint256 unlockedGenerations = tokenToUnlockedGenerations[_tokenId];
        for (uint256 i = 0; i < generations.length; ++i) {
            // decrement unlock counter so that owner may disable the generation at a later date if needed
            uint256 unlockBit = 1 << i;
            if (unlockedGenerations & unlockBit == unlockBit) {
                generations[i].unlocks--;
            }
        }

        uint256 activeGeneration = tokenToGenerationId[_tokenId];
        generations[activeGeneration].activations--;

        super._burn(_tokenId);
    }
}
