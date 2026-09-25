"""
BDD style test helper library

For more information, see https://github.com/hylom/spycy-test

Copyright (c) 2023-2026 hylom@hylom.net (Hiromichi Matsushima)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from typing import Any
import unittest
import os
import sys
import inspect

def debug(*args):
    if os.environ.get("SPICY_DEBUG"):
        i = inspect.stack()[1]
        info = "%s:%s[%s]" % (i.filename,
                              i.lineno,
                              i.function)
        del i
        print(info, *args, file=sys.stderr)

# helper function
def _to_str(x):
    if isinstance(x, str):
        return "'%s'" % x
    return str(x)


class ScenarioFailure(AssertionError):
    def __init__(self, err, fixture=None):
        super().__init__(err)
        self.fixture = fixture

    def __str__(self):
        f = self.fixture
        if not f:
            return super().__str__()

        spec = f.then._get_spec()
        return "INVALID RESULT:\n  %s\n  (%s)" % (spec, super().__str__())


class Scenario(unittest.FunctionTestCase):
    def __init__(self, testFunc, setUp=None, tearDown=None, description=None):
        super().__init__(testFunc, setUp=None, tearDown=None, description=None)
        self.description = description

    def __str__(self):
        return "Scenario: %s" % self.description


class BddTest(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        #self._define_properties()

    def runTest(self):
        pass

    def _getTestFunctions(self):
        prefix = 'scenario_'
        fn = lambda x:x.startswith(prefix)
        return [self._getTestFunction(x) for x in filter(fn, dir(self))]

    def _getTestFunction(self, method_name):
        method = getattr(self, method_name)
        if not callable(method):
            raise TypeError('%s is not callable' % prefix + scenario)
        return (lambda : self._run_test(method),
                self._method_name_to_scenario(method_name))

    def _method_name_to_scenario(self, name):
        prefix = 'scenario_'
        terms = name[len(prefix):].split("_")
        return " ".join([t[0].upper() + t[1:] for t in terms])

    def _run_test(self, method):
        f = TestCaseFixture(self)
        self.current_fixture = f
        self.setUp()
        try:
            method(f.given, f.when, f.then)
        except AssertionError as e:
            self.tearDown()
            raise ScenarioFailure(e, f) from e
        except Exception as e:
            self.tearDown()
            debug("error: %s" % e)
            raise e from e
        self.tearDown()
        del self.current_fixture

    def run(self, result=None):
        if not result:
            result = self.defaultTestResult()

        # run test
        tests = [Scenario(fn, description=desc)
                 for (fn, desc)
                 in self._getTestFunctions()]
        if not tests:
            return result
        suite = unittest.TestSuite(tests)
        self.setUpClass()
        suite.run(BddTestResult(result))
        self.tearDownClass()
        return result

    def _define_properties(self):
        self._properties = {}
        prefix = 'define_'
        fn = lambda x:x.startswith(prefix)
        for method_name in filter(fn, dir(self)):
            method = getattr(self, method_name)
            property_name = method_name[len(prefix):]
            if not property_name:
                continue
            if not callable(method):
                raise TypeError('%s is not callable' % method_name)
            self._properties[property_name] = method()


class BddTestResult():
    def __init__(self, result):
        self._result = result

    def __getattr__(self, key):
        return getattr(self._result, key)

    def addFailure(self, test, err):
        (t, v, trace) = err
        formatted_err = v
        self.failures.append((test, formatted_err))


class Fixture(object):
    def __init__(self):
        self._given = Given(self)
        self._when = When(self)
        self._then = Then(self)

    @property
    def given(self):
        return self._given

    @property
    def when(self):
        return self._when

    @property
    def then(self):
        return self._then


class TestCaseFixture(Fixture):
    def __init__(self, testcase):
        super().__init__()
        self._testcase = testcase

    def __getattr__(self, key):
        return getattr(self._testcase, key)


class Given():
    def __init__(self, fixture):
        self._fixture = fixture
        self._dict = {}

    def __call__(self, **kwargs):
        self._dict.update(kwargs)

    def __getattr__(self, key):
        v = self._dict[key]
        return Given.Value(key, v)

    def __getitem__(self, key):
        v = self._dict[key]
        return Given.Value(key, v)

    class Value():
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def __getitem__(self, index):
            name = "%s[%s]" % (self.name, _to_str(index))
            return Given.Value(name, self.value[index])

        def __getattr__(self, name):
            new_name = "%s.%s" % (self.name, name)
            return Given.Value(new_name, getattr(self.value, name))


class When():
    def __init__(self, fixture):
        self._fixture = fixture
        self._stack = []
        self._executed = False
        self._spec = ""

        self._this = None
        self._spec_stack = []

    def __getattr__(self, key):
        debug("when.__getattr__(%s)" % key)
        t = When.Term(self, key)
        self._stack.clear()
        self._spec = ""
        self._executed = False
        self._stack.append(t)
        return t

    def _eval(self):
        if self._executed:
            debug("'when' stack is already executed. skip.")
            return

        this = None
        spec = []
        given = self._fixture.given
        debug("start execution 'when' stack...")
        debug("'when' stack: %s" % self._stack)
        debug("'given' stack: %s" % given._dict)
        for term in self._stack:
            debug("term: %s, this: %s" % (term._name, this))
            if term._name == "_and":
                spec.append("and")
                continue
            if this is not None:
                p = getattr(this, term._name)
            else:
                # no current item, so get from given values
                try:
                    p = given[term._name].value
                except KeyError as err:
                    raise AttributeError(err)

            # if term is not callable, process next term
            if not term._callable:
                this = p
                spec.append(term._name)
                continue
            # call the function
            arg_names = []
            # convert arguments list
            args = []
            if term._args:
                for i in term._args:
                    if isinstance(i, Given.Value):
                        args.append(i.value)
                        arg_names.append(_to_str(i.value))
                    else:
                        args.append(i)
                        arg_names.append(_to_str(i))
                        
            # convert keywork arguments
            kwargs = {}
            if term._kwargs:
                for i in term._kwargs.keys():
                    if isinstance(i, Given.Value):
                        kwargs[i] = term._kwargs[i].value
                        arg_names.append("%s=%s" % (i, _to_str(term._kwargs[i].value)))
                    else:
                        kwargs[i] = term._kwargs[i]
                        arg_names.append("%s=%s" % (i, _to_str(term._kwargs[i])))
            # call and append
            p = p(*args, **kwargs)
            spec.append("%s(%s)" % (term._name, ", ".join(arg_names)))
            this = p
        self._it = p
        self._spec = " ".join(spec)
        self._executed = True
        debug("finish execution 'when' stack.")
        debug("'when' spec is: %s" % self._fixture.when._spec)
        debug("'it' is: %s" % self._it)

    class Term():
        def __init__(self, when, name):
            self._when = when
            self._name = name
            self._callable = False

        def __getattr__(self, key):
            t = When.Term(self._when, key)
            self._when._stack.append(t)
            return t

        def __call__(self, *args, **kwargs):
            self._callable = True
            self._args = args
            self._kwargs = kwargs
            return self

        def __repr__(self):
            name = self._name
            if self._callable:
                name = name + "()"
            return "<When.Term: '%s'>" % name


class Then():
    def __init__(self, fixture):
        self._fixture = fixture
        self._clear()
        self._cursor = None

    def _clear(self):
        self._spec = []
        self._current_spec = 0

    def _get_spec(self):
        when_spec = self._fixture.when._spec
        return ("when %s, then %s" % (when_spec, "".join(self._spec))).strip()

    def _get_current_spec(self):
        spec = self._spec[self._current_spec:]
        return "".join(spec).strip()

    def __getattr__(self, key):
        self._clear()
        self._fixture.when._eval()
        self._it = self._fixture.when._it
        self._spec.append(key)

        try:
            p = self._fixture.given[key].value
        except KeyError as err:
            raise AttributeError(key) from err
        t = It(p, key, self)
        return t

    @property
    def it(self):
        self._clear()
        self._fixture.when._eval()
        self._it = self._fixture.when._it
        self._spec.append('it')
        it = It(self._it, 'it', self)
        return it

    @property
    def the(self):
        return self._cursor


class It():
    CHAINS = set(["to", "be", "been", "is", "that", "which",
                  # "and" has special mean in spicy 
                  "has", "have", "with", "at", "of",
                  "same", "but", "does", "still", "also",
                  # below is additional keyword in spicy
                  "should", "value",
                  ])

    def __init__(self, value, name, parent):
        self._value = value
        self._name = name
        self._parent = parent
        self._exception = None

    def _check_exception(self):
        if self._exception:
            raise self._exception

    def __getattr__(self, name):
        debug(f"attr: {name}")
        if hasattr(self._value, name):
            v = getattr(self._value, name)
            self._parent._spec.append(".%s" % name)
            return It(v, name, self._parent)
        return self._chain_or_execute(name)

    def _chain_or_execute(self, name):
        debug(f"chain: {name}")
        name = name.strip("_")
        if not name in self.CHAINS:
            self._check_exception()
            raise AttributeError(name)
        self._parent._spec.append(" %s" % name)
        return self

    def __getitem__(self, name):
        self._check_exception()
        v = self._value[name]
        self._parent._spec.append("{}[{}]".format(self._name, name))
        return It(v, name, self._parent)

    def __call__(self, *args, **kwargs):
        self._check_exception()
        if not callable(self._value):
            raise TypeError("%s is not callable" % self._value.__name__)
        specs = []

        # convert GivenValue to the value
        for arg in args:
            if isinstance(arg, Given.Value):
                specs.append("%s" % _to_str(arg.value))
            else:
                specs.append("%s" % _to_str(arg))
        args = [x.value if isinstance(x, Given.Value) else x for x in args]

        for k in kwargs.keys():
            if isinstance(kwargs[k], Given.Value):
                specs.append("%s=%s" % (k, _to_str(kwargs[k].value)))
                kwargs[k] = kwargs[k].value
            else:
                specs.append("%s=%s" % (k, _to_str(kwargs[k])))
                kwargs[k] = kwargs[k]

        debug("value: %s" % self._value)
        debug("args: %s" % args)
        debug("kwargs: %s" % kwargs)
        name = "(%s)" % ", ".join(specs)
        self._parent._spec.append(name)

        try:
            v = self._value(*args, **kwargs)
        except Exception as e:
            it = It(None, name, self._parent)
            it._exception = e
            return it

        return It(v, name, self._parent)

    @property
    def _and(self):
        self._check_exception()
        self._parent._spec.append(" and")
        self._parent._current_spec = len(self._parent._spec)
        if hasattr(self, "_target"):
            del self._target
        self._parent._cursor = self
        return self._parent

    @property
    def length(self):
        self._check_exception()
        self._parent._spec.append(" length")
        self._target = len(self._value)
        return self

    def applied_to(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" applied to")
        self._parent._spec.append(" %s" % _to_str(value))

        self._target = value(target)
        return self
        

    def instance(self, the_type):
        self._check_exception()
        self._parent._spec.append(" instance of %s" % the_type)
        self._parent._fixture.assertIsInstance(self._value,
                                             the_type,
                                             self._get_spec())
        return self

    def has_property(self, value):
        self._check_exception()
        self._parent._spec.append(" property")
        self._parent._spec.append(" %s" % _to_str(value))
        self._parent._fixture.assertIn(value, self._value, self._get_spec())
        return self

    def length_of(self, value):
        self._check_exception()
        self._parent._spec.append(" length of")
        self._parent._spec.append(" %s" % _to_str(value))
        self._parent._fixture.assertEqual(len(self._value),
                                          value, self._get_spec())
        return self

    def equal(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" equal")
        self._parent._spec.append(" %s" % _to_str(value))
        
        self._parent._fixture.assertEqual(target, value, self._get_spec())
        return self

    def _raise(self, value):
        self._parent._spec.append(" raises %s" % value.__name__)
        if not self._exception:
            msg = "%s not raised: %s" % (value, self._get_spec())
            raise self._parent._fixture.failureException(msg)
        e = self._exception
        if not isinstance(e, value):
            msg = "%s not raised but %s: %s" % (value, e, self._get_spec())
            raise self._parent._fixture.failureException(msg)
        self._exception = None
        return self

    def not_raise(self, value):
        self._parent._spec.append(" not raises %s" % value.__name__)
        if not self._exception:
            return self
        e = self._exception
        if isinstance(e, value):
            msg = "%s raised : %s" % (value, e, self._get_spec())
            raise self._parent._fixture.failureException(msg)
        self._exception = None
        return self

    @property
    def none(self):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        self._parent._spec.append(" is None")
        self._parent._fixture.assertIsNone(target, self._get_spec())
        return self

    @property
    def true(self):
        debug("true")
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        self._parent._spec.append(" is True")
        self._parent._fixture.assertTrue(target, self._get_spec())
        return self

    @property
    def false(self):
        debug("false")
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        self._parent._spec.append(" is False")
        self._parent._fixture.assertFalse(target, self._get_spec())
        return self

    def greater_equal(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" greater equal")
        self._parent._spec.append(" %s" % _to_str(value))
        
        self._parent._fixture.assertGreaterEqual(target, value, self._get_spec())
        return self

    def less_equal(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" less equal")
        self._parent._spec.append(" %s" % _to_str(value))
        
        self._parent._fixture.assertLessEqual(target, value, self._get_spec())
        return self

    def greater_than(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" greater than")
        self._parent._spec.append(" %s" % _to_str(value))
        
        self._parent._fixture.assertGreater(target, value, self._get_spec())
        return self

    def less_than(self, value):
        self._check_exception()
        if hasattr(self, "_target"):
            target = self._target
        else:
            target = self._value
        if isinstance(value, Given.Value):
            value = value.value
        self._parent._spec.append(" less than")
        self._parent._spec.append(" %s" % _to_str(value))
        
        self._parent._fixture.assertLess(target, value, self._get_spec())
        return self

    def at(self, value):
        self._check_exception()
        self._parent._spec.append(" at")
        self._parent._spec.append(" %s" % _to_str(value))
        self._target = self._value[value]
        return self

    def _get_spec(self):
        return self._parent._get_current_spec()

    class InvalidGrammar(Exception):
        pass
                            

