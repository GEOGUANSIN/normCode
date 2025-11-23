# NormCode Guide - Reference of Concepts

While concepts define the structure of a NormCode plan, the actual information is stored in a **Reference**. Understanding the Reference is key to grasping how data is stored, manipulated, and flows through the plan.

A Reference is the container where the information for a concept is kept. Specifically, it is the **semantical concepts** (like `{object}`, `[]`, or `<>`) that have an associated Reference, as they represent the data-holding entities within the plan.

**Key Characteristics of a Reference:**

-   **Multi-dimensional Container**: A Reference is multi-dimensional because a concept can exist in multiple contexts. Each context can introduce a new dimension, allowing the Reference to hold different instances or elements of the concept's information in a structured way.
-   **Named Axes**: Each dimension, often corresponding to a specific context, is represented as a named **axis**. This allows for clear organization and retrieval of information. For example, a concept like `{grade}` could have a Reference with axes named `student` and `assignment`, representing the different contexts in which a grade exists.
-   **Shape**: The size of each dimension defines the `shape` of the information within the Reference.
-   **Data Manipulation**: The core logic of the **Agent's Sequences** (e.g., collecting items with `grouping` or accumulating results with `quantifying`) involves manipulating the information held within these References.

In short, a `Concept` gives information its meaning within the plan, while a `Reference` provides the structure to hold and organize that information.


