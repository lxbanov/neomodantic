import types
from pydantic import BaseModel, ConfigDict

from neomodel.exceptions import RequiredProperty
from neomodel.properties import AliasProperty, Property


def display_for(key):
    def display_choice(self):
        return getattr(self.__class__, key).choices[getattr(self, key)]

    return display_choice

class PropertyManager(BaseModel):
    """
    Common methods for handling properties on node and relationship objects.
    """
    
    model_config = ConfigDict(extra='allow')

    def __init__(self, **kwargs):
        # To initialize the BaseModel correctly
        super().__init__(**kwargs)
        properties = getattr(self, "__all_properties__", None)
        if properties is None:
            properties = self.defined_properties(rels=False, aliases=False).items()
        for name, property in properties:
            if kwargs.get(name) is None:
                if getattr(property, "has_default", False):
                    setattr(self, name, property.default_value())
                else:
                    setattr(self, name, None)
            else:
                setattr(self, name, kwargs[name])

            if getattr(property, "choices", None):
                setattr(
                    self,
                    f"get_{name}_display",
                    types.MethodType(display_for(name), self),
                )

            if name in kwargs:
                del kwargs[name]

        aliases = getattr(self, "__all_aliases__", None)
        if aliases is None:
            aliases = self.defined_properties(
                aliases=True, rels=False, properties=False
            ).items()
        for name, property in aliases:
            if name in kwargs:
                setattr(self, name, kwargs[name])
                del kwargs[name]

        # undefined properties (for magic @prop.setters etc)
        for name, property in kwargs.items():
            setattr(self, name, property)

    @property
    def __properties__(self):
        from neomodel.sync_.relationship_manager import RelationshipManager

        return dict(
            (name, value)
            for name, value in vars(self).items()
            if not name.startswith("_")
            and not callable(value)
            and not isinstance(
                value,
                (
                    RelationshipManager,
                    AliasProperty,
                ),
            )
        )

    @classmethod
    def deflate(cls, properties, obj=None, skip_empty=False):
        """
        Deflate the properties of a PropertyManager subclass (a user-defined StructuredNode or StructuredRel) so that it
        can be put into a neo4j.graph.Entity (a neo4j.graph.Node or neo4j.graph.Relationship) for storage. properties
        can be constructed manually, or fetched from a PropertyManager subclass using __properties__.

        Includes mapping from python class attribute name -> database property name (see Property.db_property).

        Ignores any properties that are not defined as python attributes in the class definition.
        """
        deflated = {}
        for name, property in cls.defined_properties(aliases=False, rels=False).items():
            db_property = property.get_db_property_name(name)
            if properties.get(name) is not None:
                deflated[db_property] = property.deflate(properties[name], obj)
            elif property.has_default:
                deflated[db_property] = property.deflate(property.default_value(), obj)
            elif property.required:
                raise RequiredProperty(name, cls)
            elif not skip_empty:
                deflated[db_property] = None
        return deflated

    @classmethod
    def inflate(cls, graph_entity):
        """
        Inflate the properties of a neo4j.graph.Entity (a neo4j.graph.Node or neo4j.graph.Relationship) into an instance
        of cls.
        Includes mapping from database property name (see Property.db_property) -> python class attribute name.
        Ignores any properties that are not defined as python attributes in the class definition.
        """
        inflated = {}
        for name, property in cls.defined_properties(aliases=False, rels=False).items():
            db_property = property.get_db_property_name(name)
            if db_property in graph_entity:
                inflated[name] = property.inflate(
                    graph_entity[db_property], graph_entity
                )
            elif property.has_default:
                inflated[name] = property.default_value()
            else:
                inflated[name] = None
        return cls(**inflated)

    @classmethod
    def defined_properties(cls, aliases=True, properties=True, rels=True):
        from neomodel.sync_.relationship_manager import RelationshipDefinition
        from neomodel.sync_.core import Property

        props = {}

        for baseclass in reversed(cls.__mro__):
            props.update(
                dict(
                    (name, property)
                    for name, property in vars(baseclass).items()
                    if (aliases and isinstance(property, AliasProperty))
                    or (
                        properties
                        and isinstance(property, Property)
                        and not isinstance(property, AliasProperty)
                    )
                    or (rels and isinstance(property, RelationshipDefinition))
                )
            )

            if issubclass(baseclass, BaseModel):
                for key, field in baseclass.model_fields.items():
                    if isinstance(field.default, RelationshipDefinition) and rels:
                        props[key] = field.default
                    if isinstance(field.default, Property) and properties:
                        props[key] = field.default
                    if isinstance(field.default, AliasProperty) and aliases:
                        props[key] = field.default
                        
        return props
