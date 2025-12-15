This document provides a guide to the operators used in "normcode" for defining concepts and actions, based on the examples in `refined_translation_algorithm.txt`.

The operators are divided into two main categories: those for "object-like" concepts and those for "action-like" concepts.

### Object-Like Concept Operators

These operators are used to define, specify, and manipulate concepts that represent things or objects.

*   `$.`: **Specification**: Defines a concept by relating it to another, more general concept. For example, a `{user account}` is specified as a type of `{record}`.
*   `$::`: **Nominalization**: Transforms a process or action into a noun or object. `User Authentication` is defined as the nominalization of the action "verify the user's identity."
*   `$+`: **Continuation**: Extends an existing concept or sequence. An `{updated sequence of numbers}` is a continuation of an `{old sequence of numbers}`.
*   `$%`: **Abstraction**: Defines a concept by enumerating its specific instances. A `{number sequence}` is defined by listing the numbers `[1, 2, 3, 4, 5]`.
*   `$=`: **Identity**: Asserts that a concept is identical to a specific marked instance of itself.
*   `&in`: **Annotation Grouping**: Groups related data together, like creating a list of key-value pairs. It groups `{value}` and `{position}` into an indexed list.
*   `&across`: **Order Grouping**: Concatenates or combines ordered concepts. A `{number sequence}` is formed by combining `{number sequence 1}` and `{number sequence 2}`.
*   `::({})`: **Unbounded Imperative**: Describes a method or action that can be performed on or by an object, where the action itself is defined inline. For instance, finding a `{the user}` is done by the action `find user by {name}`.
*   `:_:{}({})`: **Bounded Imperative**: Similar to the unbounded imperative, but the action is defined by a separate, reusable concept. Finding `{the user}` is done via a predefined `{find}` method.
*   `:>:()`: **Input Imperative**: Represents an action where data is received as input, such as getting a `{user name}` from the user.
*   `:<:()`: **Output Imperative**: Represents an action that produces an output, like outputting a `{user name}`.
*   `::<{}>`: **Unbounded Judgement**: Represents a boolean state or condition about a concept, like `<user is an admin>`.
*   `::{}({}):`: **Quantifier Judgement**: A more complex judgement that involves a quantifier (e.g., `All`) to make a statement about a collection of things.
*   `*every`: **Listing/Quantifying**: Applies an operation to each item in a collection, such as squaring `*every` number in a sequence.

### Action-Like Concept Operators

These operators are used to define the logic, methods, and conditions related to actions.

*   `@by`: **Method**: Specifies the means or method by which an action is performed. `Authenticate the user` is done `@by` checking their password.
*   `@if`: **Conditional**: Executes an action only if a certain condition is true. The admin dashboard is shown `@if` the user is an admin.
*   `@if!`: **Negative Conditional**: Executes an action only if a certain condition is false.
*   `@after`: **Sequence**: Specifies that an action occurs after another event or action has completed.

**Note on the `@after` operator:**
There appears to be a potential point of confusion in the original example for the `@after` operator. The prose says, "Show the admin dashboard **after the user is authenticated**," but the code example is ` <= @after({admin dashboard})`, which seems circular. Based on the description, one might expect something more like `@after(::(Authenticate the user))` to indicate the dependency.

---

### Normcode Operator Examples

#### Example of finding an operator for an object-like concept:


1. Specification of object-like concept ($.):  

```normcode
:<:({user account})
    ...: A user account is a record containing a username and password.
    ?: What is a user account?
    <= $.({record})
        /: It is specified as a record among components.
    <- {record}
        ...: A record containing a username and password.
    <- {username}
        ...: A username for the user account.
    <- {password}
        ...: A password for the user account.
```

Comment: A key insight from this example is how the `$.` operator functions. While `{record}`, `{username}`, and `{password}` are all defined as components of the `{user account}`, only the `{record}` concept is passed up as the direct result of the specification to its parent. The other concepts serve as contextual details of that specification.

2. Nominalization of object-like concept ($::):

```normcode
:<:({User Authentication})
    ...: User authentication is the process of verifying a user's identity.
    ?: What is user authentication?
    <= $::
        /: It is defined as a process.
    <- ::(verify the user's identity)
        ...: The action is to verify the user's identity.
```

Comment: Here, the "User Authentication" is a nominalized concept of a process. The `$::` operator is used to formally convert this imperative concept into a machine-readable object, `{User Authentication}`.


3. Continuation of object-like concept ($+):

```normcode
:<:({updated sequence of numbers})
    ...: The updated sequence of numbers is the result of adding the new number to the old sequence of numbers.
    ?: What is the updated sequence of numbers?
    <= $+({new number}:{old sequence of numbers})
        /: It is the result of adding 1 to the old sequence of numbers.
    <- {new number}
        ...: The new number is the number to add to the old sequence of numbers.
    <- {old sequence of numbers}
        ...: The old sequence of numbers is the sequence of numbers before adding the new number.
```

Comment: Here, the "updated sequence of numbers" is a continuation of a sequence of numbers. The `$+` operator is used to formally add instances to the existing instances of the concept.

4. Abstraction of object-like concept ($%):
```normcode
:<:({number sequence})
    ...: The number sequence is 1, 2, 3, 4, 5.
    ?: What are all numbers?
    <= $%({number sequence})
        /: It is the abstraction of the sequence of numbers.
    <- [{1}, {2}, {3}, {4}, {5}]
        ...: The number sequence is 1, 2, 3, 4, 5.
```

Comment: Here, the "number sequence" is an abstraction of a sequence of numbers. The `$%` operator is used to formally write this object by instances directly.


5. Identity of object-like concept ($=):
```normcode
:<:({number sequence})
    ...: The number sequence is marked by {1}.
    ?: What is the number sequence?
    <= $={1}
        /: It is identical to itself as where marked by {1}
```

Comment: Here, the "number sequence" is an identity of itself. The `$=` operator is used to formally mark the concept as identical to itself as where marked by {1}.

6. Annotation grouping of object-like concept (&in):
```normcode
:<:([{value} with {position} indexed]) |ref. [{position: 1, value: 23}, {position: 2, value: 34}]
    ...: The value with position indexed is the sequence of numbers indexed by their position and value.
    ?: What is the value with position indexed?
    <= &in[{position}; {value}]
        /: It is grouped as a sequence of numbers, where position and value are complementary. 
    <- {position} |ref. [1, 2]
        ...: The position is the position of the number in the indexed number sequence.
    <- {value} |ref. [23, 34]
        ...: The value is the value of the number in the indexed number sequence.
```

Comment: Here, the "value with position indexed" is an annotated grouping of the "value" by its position. The `&in` operator is used to formally group the concept by its position and value.



7. Order grouping of object-like concept (&across):
```normcode
:<:({number sequence}) |ref. [1, 2, 3, 4, 5]
    ...: The number sequence is the combination of the number sequence 1 and the number sequence 2.
    ?: What is the number sequence?
    <= &across({number sequence})
        /: It is across the sequence of numbers.
    <- {number sequence 1} |ref. [1, 2, 3]
        ...: The number sequence 1 is 1, 2, 3.
    <- {number sequence 2} |ref. [4, 5]
        ...: The number sequence 2 is 4, 5.
```

Comment: Here, the "number sequence" is a across of the "number sequence 1" and the "number sequence 2". The `&across` operator is used to formally across the concept by its position and value.



8. Method of object-like concept unbounded imperative (::({})):


```normcode
:<:({the user})
    ...: Find the user with their name.
    ?: How do you find the user?
    <= ::(find user by {name})
        ...: It is done by finding the user by their name.
    <- {name}
        ...: The name of the user to be found.
```

Comment: Here, the "user" is a imperative of the "user with name". The `::({})` operator is used to formally imperative the concept by its user with name.


9. Method of object-like concept bounded imperative (:_:{}({})):

```normcode
:<:({the user})
    ...: Find the user with their name according to the definition of the finding.
    ?: How do you find the user?
    <= :_:{find}({user name})
        ...: It is done by finding the user by their name.
    <- {user name}
        ...: The name of the user to be found.
    <- {find}
        ...: The definition of the finding.
```

Comment: Here, the "user" is a bounded imperative of the "user with name". The `::{find}({user name})` operator is used to formally imperative the concept by its user with name according to the definition of the finding.

10. Method of object-like concept input imperative (:>:()):


```normcode
:<:({user name})
    ...: the user name is inputed by the user.
    ?: How do you input the user name?
    <= :>:{user name}?()
        /: It is done by inputing the user name.
    <- {user name}?
        /: The definition of the user name.
```

comment: Here, the "user name" is a input of the "user". The `:>:{user name}?()` operator is used to formally input the concept by its user name.


11. Method of object-like concept output imperative (:<:()):


```normcode
:<:({outputing})
    ...: the user name is outputed by the user.
    ?: How do you output the user name?
    <= $::
        /: Outputing is defined as a process.
    <- :<:({user name})
        /: It is done by outputing the user name.
    <- {user name}
        ...: The user name to be outputed.
```


12. Method of object-like concept unbounded judgement (::<{}>):

```normcode
:<:(<user is an admin>)
    ...: The user is an admin.
    ?: What is the user?
    <= ::<{user} is an admin>
        ...: It is a judgement that the user is an admin.
    <- {user}
        ...: The user to be judged.
```


Comment: Here, the "user is an admin" is a judgement of the "user" being an admin. The `::<{}>` operator is used to formally judge the concept by its user.


13. Method of object-like concept quantifier judgement (::{}({})):

```normcode
:<:(<everything is on the table>)
    ...: Everything is on the table.
    ?: How to judge everything?
    <= ::{All%(True)}<{things} on the table>
        ...: It is done by quantifying the everything, and checking if the things are on the table.
    <- {things}
        ...: The things to be checked.
```
Comment: Here, the "everything is on the table" is a quantifier judgement of the "things" being on the table. The `::{All%(True)}<{things} on the table>` operator is used to formally judge the concept by its things being on the table.


14. Listing/quantifying of object-like concept (*every):
```normcode
:<:({number sequence squared}) |ref. [4, 9, 16, 25]
    ...: The number sequence squared is the sequence of numbers squared.
    ?: What is the number sequence squared?
    <= *every({number sequence})
        ...: It is done on each of the sequence of numbers, where the number is squared.
    <- {number sequence} |ref. [2, 3, 4, 5]
        ...: The number sequence is 2, 3, 4, 5.
```


#### Example of finding an operator for an action-like concept:


1. Method of action-like concept (@by):

```normcode
:<:(::(Authenticate the user))
    ...: Authenticate the user by checking their password.
    ?: How do you authenticate the user?
    <= @by(:_:)
        /: It is done by a method.
    <- :_:{check password}({user})
        ...: by checking their password.
    <- {check password}
        ...: The definition of the checking password.
    <- {user}
        ...: The user to be authenticated.
```

2. Conditional for a concept (@if):

```normcode
:<:(::(Show the admin dashboard))
    ...: Show the admin dashboard if the user is an admin.
    ?: When do you show the admin dashboard?
    <= @if(<user is an admin>)
        /: It is done only if the user is an admin.
    <- <user is an admin>
        ...: if the user is an admin.
```

3. Conditional for a concept (@if!):

```normcode
:<:(::(Show the admin dashboard))
    ...: Show the admin dashboard if the user is not an admin.
    ?: When do you show the admin dashboard?
    <= @if!(<user is not an admin>)
        /: It is done only if the user is not an admin.
    <- <user is not an admin>
        ...: if the user is not an admin.
```

4. Conditional for a concept (@after):

```normcode
:<:(::(Show the admin dashboard))
    ...: Show the admin dashboard after the user is authenticated.
    ?: When do you show the admin dashboard?
    <= @after({admin dashboard})
        /: It is done after the admin dashboard is shown.
    <- {admin dashboard}
        ...: The admin dashboard to be shown.
```
