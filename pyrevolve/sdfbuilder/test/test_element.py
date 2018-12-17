from sdfbuilder import Element
import unittest


class A(Element):
    pass


class B(Element):
    pass


class C(B):
    pass


class TestElement(unittest.TestCase):
    def test_filter(self):
        root = Element()
        sub1 = A()
        sub2 = B()

        sub1a = A()
        sub1b = B()
        sub1c = C()
        sub2a = A()
        sub2b = B()

        sub2ab = B()

        sub1.add_elements([sub1a, sub1b, sub1c])
        sub2.add_elements([sub2a, sub2b])
        sub2a.add_element(sub2ab)
        root.add_elements([sub1, sub2])

        check = root.get_elements_of_type(B, recursive=False)
        self.assertEquals([sub2], check)

        check = root.get_elements_of_type(B, recursive=True)
        self.assertEquals([sub1b, sub1c, sub2, sub2ab, sub2b], check)

if __name__ == '__main__':
    unittest.main()
