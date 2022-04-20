## This implementation is based on @NFTChance's Non-dilutive ERC721 using Mimetic Metadata.

Please read the original documentation as it explains the concept very well.

https://github.com/nftchance/nft-nondilutive/

## Features and differences in this implementation:

- Mimetic NFT contract allows NFT holders to own multiple generations or "faces" for their NFT. NFTChance also calls them layers. I like to think of them as faces. Like the Faceless Men from Game of Thrones, the owners of mimetic NFTs can choose the face to wear at any point in time.
- Zeroth generation is the default and gets unlocked when the NFT is minted.
- Contract owner may choose to add new generations which define:
  - A prerequisite generation. This is a generation the user must own prior to being able to unlock that generation. This allows for tree-like generation dependencies. E.g. you could have a base character in your game which can later specialize in different elements, say fire and water. And you could make new specialization like shadowfire, which will require having fire as well.
  - Cost to unlock the generation. Once unlocked, the token owner is free to switch generations as they wish. If the cost is zero, the generation is considered auto-unlocked if the owner has unlocked the prerequisite generation. Auto-unlocked generations may not set prerequisite to another auto-unlock generation. This was done to avoid cascading checks for unlock status.
  - Contract tracks the number of unlocks (purchases) and active tokens for each generation. The owner may disable and then change generation properties before any unlocks are done (for unlockable generations) or while no tokens are actively using it (auto-unlock generations).
  - Disabled generations may not be unlocked or activated.
  - BaseURI for the generation may be changed while enabled, and this was left only to facilitate the generation "reveal" ceremonies.
  - Availability flag is added to facilitate limited-time offering generations. Unavailable generations may not be unlocked any more, but if they were previously unlocked they can be activated.

Feel free to add/change/remove any piece to suit your needs. If you have any comments, ideas or concerns I would love to hear them.

#

# Dev

Recommended with Docker: you can use my brownie image _zhranj/brownie_

## Running tests

docker> brownie test

==================================== test session starts ========================================\
platform linux -- Python 3.7.13, pytest-6.2.5, py-1.11.0, pluggy-1.0.0\
rootdir: /code/mimeticerc721\
plugins: eth-brownie-1.18.1, forked-1.4.0, hypothesis-6.27.3, web3-5.27.0, xdist-1.34.0\
collected 81 items\
\
Launching 'ganache-cli --port 8545 --gasLimit 12000000 --accounts 10 --hardfork istanbul --mnemonic brownie'...\
\
tests/test_mimetic_erc721.py ................................................................................. [100%]\
\
================================== 81 passed in 61.84s (0:01:01) ===================================
