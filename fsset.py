"""
A file saving set (FSSet) that writes the set to disk automatically. 
Supports __contains__ and add () in O(1) time.

@author: Adhiraj Singh

"""
from os import remove, path

class FSSet:
    def __init__ (self, filename: str):
        self.filename = filename
        self.set = set ()
        self.load ()
    def load (self):
        if path.isfile (self.filename):
            with open (self.filename, "r") as f:
                lines = f.read ().split ("\n") # separate elements by line
                if lines[-1] == "": # do not add the last line if its empty
                    lines = lines[:-1]
                self.set = set (lines)
    
    def add (self, item: str):
        if item not in self:
            self.set.add (item)
            with open (self.filename, "a") as f:
                f.write (item + "\n")
    def clear (self):
        self.set.clear ()
        if path.isfile (self.filename):
            remove (self.filename)
    def __contains__ (self, item: str):
        return item in self.set

def test_fsset ():
    """ A small unit test for FSSet """
    print ("testing fsset")

    lines = ["hello", "this", "is", "a", "test", "file", "with", "many", "lines"]
    fsset = FSSet ("test_file.csv")
    
    fsset.clear ()
    assert len (fsset.set) == 0 # verify clear works

    for line in lines:
        fsset.add (line) # add all the lines
    for line in lines:
        assert line in fsset # verify they got added

    fsset2 = FSSet ("test_file.csv") # open another set with the same file
    assert len (fsset.set) == len(fsset2.set)
    for line in lines:
        assert line in fsset2 # verify that lines loaded correctly

if __name__ == "__main__":
    test_fsset ()