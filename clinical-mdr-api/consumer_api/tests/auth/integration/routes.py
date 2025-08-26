"""
This list must contain all routes of the main application as (path:str, method:str, required_roles:Set[str])
"""

ALL_ROUTES_METHODS_ROLES = (
    ("/v1/studies", "GET", {"Study.Read"}),
    ("/v1/studies/{uid}/study-visits", "GET", {"Study.Read"}),
    ("/v1/studies/{uid}/study-activities", "GET", {"Study.Read"}),
    ("/v1/studies/{uid}/study-activity-instances", "GET", {"Study.Read"}),
    ("/v1/studies/{uid}/operational-soa", "GET", {"Study.Read"}),
    ("/v1/studies/{uid}/detailed-soa", "GET", {"Study.Read"}),
    ("/v1/papillons/soa", "GET", {"Study.Read"}),
    ("/v1/library/activities", "GET", {"Library.Read"}),
    ("/v1/library/activity-instances", "GET", {"Library.Read"}),
)
