CXX = clang++
CXXFLAGS = `llvm-config --cxxflags`
LDFLAGS = `llvm-config --ldflags`
LIBS = `llvm-config --system-libs --libs all`
SRC = assembly.cpp core.cpp initfini.cpp module.cpp value.cpp \
	  executionengine.cpp transforms.cpp passmanagers.cpp targets.cpp dylib.cpp
OUTPUT = libllvmlite.dylib

all: $(SRC)
	$(CXX) -dynamiclib $(CXXFLAGS) $(SRC) -o $(OUTPUT) $(LDFLAGS) $(LIBS)


clean:
	rm -rf test
