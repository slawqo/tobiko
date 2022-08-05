.. _tobiko-reviewer-guide:

=====================
Tobiko Reviewer Guide
=====================

Document Overview
-----------------

This document describes how to review changes proposed for Tobiko. You can find
here information about where patches should be reviewed and what are some basic
rules during the review and to merge patches.

.. sidebar:: See also

   Tobiko uses `OpenStack's gerrit <https://review.opendev.org>`_ to review
   patches.
   You can find many additional details about using Gerrit in the `OpenStack
   Contributor
   Guide <https://docs.openstack.org/contributors/code-and-documentation/using-gerrit.html>`_.


Reviewing changes
-----------------

Every change proposed to one of the Tobiko repositories needs to be reviewed by
someone else. Everyone who have account in the `Openstack gerrit
<https://review.opendev.org>`_ created can review every change there.
As a reviewer You can comment on the proposed change and give one of the votes:

1. ``+1`` - when You think that change is good to be merged and don't need
   additional work,
2. ``-1`` - when change needs some additional work, You shouldn't give just
   ``-1`` to the change without any comments what is wrong in Your opinion
   there.
3. ``0`` - when You simply have some comment but don't want to give neither
   ``+1`` nor ``-1`` to the change.

Core reviewers
--------------

There is also `Core reviewers team
<https://review.opendev.org/admin/groups/4ee2829b534f7ac2695dfe4dc52885ca6f905560,members>`_.
Reviewers who are members of this team can additionally vote on the change with:

1. ``+2`` - when change is ready to be merged according to the core reviewer,
2. ``-2`` - which means ``Do not merge that change`` - it shouldn't be used
   often and only for good reason. That vote will not dissapear when new patch
   set will be proposed by the change owner. It can be only removed by the
   reviewer who gave it,
3. ``+W`` - which means that patch is approved and is going to be merged by Zuul
   after it will pass CI jobs.


To give ``+W`` to the patch and to merge it patch should have at least one
``+2`` vote for someone else than patch owner.
If the change is trivial, like e.g. fixed typo, and made by one of the Tobiko
core reviewers, it can be approved directly by the owner of the change to be
merged quickly.
Core reviewers shouldn't use that exception too much. General rule should always
be that someone else should review the change, vote with ``+2`` and approve
change with ``+W``.
