"""Session service package.

Import concrete services from their modules to avoid eager SQLAlchemy mapper
initialization when importing nested service packages.
"""
