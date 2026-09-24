---
id: insurance-locations
kind: glossary
status: active
owner: insurance-analytics@acme-insurance.test
description: "Where insured objects are: geographic location, address, city, state, zip code, latitude and longitude."
triggers:
  - location
  - address
  - city
  - state
  - zip code
  - postal code
  - country
  - latitude
  - longitude
  - where
  - insured location
  - property
source_refs:
  - docs/data.world_P&C_Insurance_Ontology_V1.r2rml (Location mapping: address lines, city, state, zip code, country, latitude, longitude; InsurableObject hasLocation)
---
# Locations

- A **location** (ontology Location) is a `geographic_location` row joined to its address and
  coordinates:
  `geographic_location JOIN location_address USING (Location_Address_Identifier)
  JOIN pysical_location USING (Physical_Location_Identifier)` (the view name is spelled
  `pysical_location`).
- Location attributes and their columns:

| Business term | Column |
| --- | --- |
| Address line 1 (street) | `location_address.Line_1_Address` |
| Address line 2 | `location_address.Line_2_Address` (empty) |
| City | `location_address.Municipality_Name` |
| State | `location_address.State_Code` (also on `geographic_location.State_Code`) |
| Zip code | `location_address.Postal_Code` |
| Country | `location_address.Country_Code` |
| Latitude / longitude | `pysical_location.Latitude_Value` / `Longitude_Value` |

- An **insurable object** (the insured property) has one location:
  `insurable_object.Geographic_Location_Identifier`. The object type is empty, so the kind of
  property is not recorded.
- **Location of a policy's insured property**: policy -> `policy_coverage_detail`
  (`Insurable_Object_Identifier`) -> `insurable_object` -> location.
- **Location of a claim's loss**: `claim.Insurable_Object_Identifier` -> `insurable_object` ->
  location. `occurrences.Geographic_Location_Identifier` is empty, so use the insured object.
- `policy.Geographic_Location_Identifier` and `policy_amount.Geographic_Location_Identifier`
  are empty: there is no rating or issuing location for a policy.
- Some locations (addresses) are not attached to any insured object; "locations we insure"
  means locations reached from `insurable_object`, not every row of `geographic_location`.
- There is no region, county or territory hierarchy
  (`Parent_Geographic_Location_Identifier` is empty).
- The **Claims Register** block lists each claim's insured address (street, city, state, zip)
  from the claim's own insured object. For one claim that object belongs to a different policy
  than the coverage the claim is recorded against - see the claims skill.
