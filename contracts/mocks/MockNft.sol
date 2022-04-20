// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../MimeticERC721.sol";

contract MockNft is MimeticERC721 {
    constructor() ERC721("MockNFT", "MFT") {
        addGeneration(
              "Mock NFT"
             ,"ipfs://baseuri"
             ,75 ether  // FTM
             ,0
             ,false
        );
    }

    function generationBaseURI(uint256 _id) public view returns (string memory) {
        // for testing only
        return _generationBaseURI(_id);
    }

    function baseURI() public view returns (string memory) {
        // for testing only
        return _baseURI();
    }

    function _baseURI() internal view virtual override returns (string memory) {
        return "ipfs://ABC123/unrevealed.jpeg";
    }

    function mint(uint256 _id) public {
        _safeMint(msg.sender, _id);
    }

    function burn(uint256 _id) public {
        _burn(_id);
    }
}
