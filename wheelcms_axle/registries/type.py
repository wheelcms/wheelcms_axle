"""
    The new type registry.

    Content registers itself explicitly (if it wants to be enabled
    out of the box through INSTALLED_APPS) on startup.

    But the application is free to clear the entire registry and re-
    initialize itself: leave out specific spokes, alter spokes/
    configuration, etc.

    The new registry allows for more default settings to be set/overridden:

    - templates (with contexts)
    - workflow
    - allowed subcontent

    Spokes have defaults but the registry may provide alternative
    (overruling) settings.

    from wheelcms_axle.registries import types

    types.clear()
    types.add(
        wheelcms_spokes.page.PageType,
        workfow=SuperWorkflow,
        initial_state=SuperWorkflow.start,
        children=(),
        templates=FancyTemplate()
    )
    types[wheelcms_spokes.page.PageType].templates.add(SimpleTemplate())

    Additionally, templates can be registered outside the context of
    a type (e.g. globally), so we'll still keep an additional type registry,
    but it will be based on the new Template registration which combines
    template location, context registration

    Existing registries will function as wrappers around the new system,
    with deprecation warnings.

"""
