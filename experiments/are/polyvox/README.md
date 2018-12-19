Import the `_PolyVoxCore.so` and `PolyVoxCore.py` files from the build of PolyVox

PolyVox instructions: 
- download from `https://github.com/portaloffreedom/polyvox` branch `develop`
- you need `swig` and `python` installed (probably other dependencies as well)
- `mkdir build && cd build && cmake .. -DENABLE_BINDINGS=ON`
- you don't need `Qt`, if you want you can avoid them using `-DENABLE_EXAMPLES=OFF`
- files `_PolyVoxCore.so` and `PolyVoxCore.py` can be found in `polyvox/build/bindings/`
- I suggest you use a link
- TODO this sucks, let's install it or integrate it or something I don't know :)
    - please don't do git submodules