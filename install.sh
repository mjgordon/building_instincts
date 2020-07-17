# Is there a way to automate the CoppeliaSim download?
# Probably but should probably live in a workshop-specific script


# Terminator : Terminal emulator with built-in frames
sudo apt install terminator

# xsltproc : Applies XSLT stylesheets to XML documents
sudo apt install xsltproc

# Setup environment
# Assuming conda is already installed. Use built-in env handling instead? 
conda create -n building_instincts python=2.7
conda activate building_instincts
conda install psutil
conda install futures
conda install -c conda-forge boost=1.67.0 boost-cpp=1.67.0
conda install multineat -c conda-forge


# Build MultiNEAT from Scratch - The conda package apparently works.
#mkdir setup
#pushd setup
#git clone https://github.com/MultiNEAT/MultiNEAT.git
#cd MultiNEAT
#sed -i "10,24 {s/^/#/}" setup.py # Comment out monkey-patching for parallel compiling
#sed -i "27 {s/^/#/}" setup.py # Comment out monkey-patching for parallel compiling
#sed -i '77s/.*/            "boost_python", "boost_numpy"]/' setup.py # Fix boost versioning
#python setup.py build_ext
#python setup.py install
#popd




