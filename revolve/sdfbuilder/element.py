"""
Basic SDF builder element.
"""
from xml.sax.saxutils import quoteattr
from .util import number_format as nf
import copy


class Element(object):
    """
    Basic element class
    """

    """
    Tag name to override in subclass. If the tag name is None,
    the wrapper is not rendered.
    """
    TAG_NAME = None

    def __init__(self, **kwargs):
        """
        Create a new Element with the given attributes.

        :param tag_name: Can be used to dynamically add a tag name different
                         from the class tag name.
        :param attributes: The element attributes
        :param elements: Initial list of sub-elements
        :param body: Element body
        :return:
        """
        self.attributes = kwargs.get("attributes", {})
        self.tag_name = kwargs.get("tag_name", None)
        self.body = kwargs.get("body", "")
        self.elements = kwargs.get("elements", [])

    def add_element(self, element):
        """
        Adds a child element.
        :param element:
        :return:
        """
        self.elements.append(element)

    def add_elements(self, elements):
        """
        Convenience method to add multiple elements at once as a list.
        :param elements:
        :return:
        """
        self.elements += elements

    def has_element(self, class_type):
        """
        Returns whether or not this element contains a child
        element of the given type
        :param class_type:
        :return:
        """
        return len(self.get_elements_of_type(class_type)) > 0

    def filter_elements(self, func, recursive=False):
        """
        Returns all elements of the given class type
        :param func: Selector function or class instance
        :param recursive: Search recursively
        :return:
        :rtype: list
        """
        elements = []

        for el in self.elements:
            if func(el):
                elements.append(el)

            if recursive and hasattr(el, 'filter_elements') and callable(el.filter_elements):
                elements += el.filter_elements(func, recursive=recursive)

        return elements

    def get_elements_of_type(self, obj, recursive=False):
        """
        Returns all direct child elements of the
        given class type.
        :param obj:
        :param recursive: Search recursively
        :return: Elements matching the given type
        """
        func = lambda element: isinstance(element, obj)
        return self.filter_elements(func, recursive=recursive)

    def remove_elements(self, func, recursive=False):
        """
        Removes all elements that match the given filter function.
        :param func: Selector function or class instance
        :param recursive: Remove recursively from child elements
        :return: List of all removed elements
        :rtype: list
        """
        to_remove = self.filter_elements(func)
        for el in to_remove:
            self.elements.remove(el)

        if not recursive:
            return to_remove

        for el in self.elements:
            if hasattr(el, 'remove_elements') and callable(el.remove_elements):
                to_remove += el.remove_elements(func, recursive)

        return to_remove

    def remove_elements_of_type(self, obj, recursive=False):
        """
        Removes all elements matching the given type.
        :param obj:
        :param recursive:
        :return:
        """
        func = lambda element: isinstance(element, obj)
        return self.remove_elements(func, recursive)

    def render_attributes(self):
        """
        Returns the dictionary of attributes that should
        be rendered. You can safely add your own attributes
        to this list by calling super when overriding this
        method.
        :return:
        """
        if self.attributes is None:
            return {}
        return self.attributes.copy()

    def render_elements(self):
        """
        Returns the list of elements that should be rendered.
        :return:
        """
        return self.elements[:]

    def render_body(self):
        """
        Returns the string representation of this element's body.
        By default, this is the concatenation of all subelements.
        You can override this method to call super and add your
        own body.
        :return:
        """
        elements = self.render_elements()
        return "\n".join(str(element) for element in elements) + self.body

    def render(self):
        """
        Renders this element according to its properties.
        :return:
        """
        all_attrs = self.render_attributes()

        body = self.render_body()
        tag_name = self.get_tag_name()

        if not tag_name:
            return body
        else:
            attrs = " ".join([a+"="+quoteattr(
                # Use number format if a number is detected
                nf(all_attrs[a]) if isinstance(all_attrs[a], float) else str(all_attrs[a])
            ) for a in all_attrs])
            tag_open = tag_name + " " + attrs if len(attrs) else tag_name
            return "<%s />" % tag_open if len(body) == 0 else "<%s>%s</%s>" % (tag_open, body, tag_name)

    def get_tag_name(self):
        """
        :return:
        :rtype: str
        """
        return self.TAG_NAME if self.tag_name is None else self.tag_name

    def copy(self, deep=True):
        """
        Wrapper over __copy__()
        :return:
        """
        return copy.deepcopy(self) if deep else copy.copy(self)

    def __str__(self):
        """
        Create the XML representation of this element. By default, this
        calls `render` without arguments. The way to add just-in-time elements
        to a custom element is by overriding this to change the render call.
        :return: String XML representation
        """
        return self.render()
