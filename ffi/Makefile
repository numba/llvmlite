CXXFLAGS = `llvm-config --cppflags`
LDFLAGS = `llvm-config --ldflags`
LIBS = `llvm-config --libs all`
CXX = clang++ -stdlib=libstdc++ -mmacosx-version-min=10.6
SRC = assembly.cpp core.cpp initfini.cpp module.cpp value.cpp \
	  executionengine.cpp transforms.cpp
OUTPUT = libllvmlite.dylib

all: $(SRC)
	$(CXX) -dynamiclib $(CXXFLAGS) $(SRC) -o $(OUTPUT) $(LDFLAGS) $(LIBS)


clean:
	rm -rf test
