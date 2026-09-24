-- One row per claim with the policy the claim is made against, and that policy's agent and
-- policy holder. Rule (see the claims skill): a claim reaches its policy only through
-- claim_coverage -> policy_coverage_detail (matched on Effective_Date AND
-- Policy_Coverage_Detail_Identifier) -> policy. claim.Insurable_Object_Identifier is NOT
-- used to find the policy.
--
-- Grain: claim. It holds while each claim has one claim_coverage row (tested in
-- claim_policy.yml: unique Claim_Identifier). Roles are pivoted to one agent and one policy
-- holder per policy before joining, so nothing fans out (a policy with two agents would
-- show the lower party id; the data has one agent and one holder per policy).
with coverage as (
    select
        cc.Claim_Identifier,
        cc.Effective_Date as Coverage_Effective_Date,
        cc.Policy_Coverage_Detail_Identifier,
        pcd.Policy_Identifier
    from {{ ref('claim_coverage') }} as cc
    join {{ ref('policy_coverage_detail') }} as pcd
        on pcd.Effective_Date = cc.Effective_Date
       and pcd.Policy_Coverage_Detail_Identifier = cc.Policy_Coverage_Detail_Identifier
),
roles as (
    select
        r.Agreement_Identifier as Policy_Identifier,
        min(case when r.Party_Role_Code = 'AG' then r.Party_Identifier end) as Agent_Party_Identifier,
        min(case when r.Party_Role_Code = 'PH' then r.Party_Identifier end) as Policy_Holder_Party_Identifier
    from {{ ref('agreement_party_role') }} as r
    group by r.Agreement_Identifier
)
select
    c.Claim_Identifier,
    cov.Coverage_Effective_Date,
    cov.Policy_Coverage_Detail_Identifier,
    cov.Policy_Identifier,
    p.Policy_Number,
    ro.Agent_Party_Identifier,
    trim(ag.First_Name || ' ' || ag.Last_Name) as Agent_Name,
    ro.Policy_Holder_Party_Identifier,
    trim(ph.First_Name || ' ' || ph.Last_Name) as Policy_Holder_Name
from {{ ref('claim') }} as c
left join coverage as cov on cov.Claim_Identifier = c.Claim_Identifier
left join {{ ref('policy') }} as p on p.Policy_Identifier = cov.Policy_Identifier
left join roles as ro on ro.Policy_Identifier = cov.Policy_Identifier
left join {{ ref('person') }} as ag on ag.Person_Identifier = ro.Agent_Party_Identifier
left join {{ ref('person') }} as ph on ph.Person_Identifier = ro.Policy_Holder_Party_Identifier
