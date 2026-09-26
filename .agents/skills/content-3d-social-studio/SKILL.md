---
name: content-3d-social-studio
description: >-
  Produces reusable 3D web experiences and social-media creative workflows with
  Three.js, Canva, Runway, and Windsor.ai. Use for campaign assets, social
  formats, 3D landing-page motion, or approved publishing and ads operations.
---

# Content 3d Social Studio

Use this skill to turn a campaign brief into an approved creative package, a
responsive 3D web scene, or a connected publishing/ads workflow. It does not
grant permission to publish, spend budget, upload a private asset, or alter a
live campaign.

## Route the request

- **3D web or supplied GLB/GLTF asset:** read [Three.js snippets](references/threejs-snippets.md). Prefer a bounded, responsive scene with an accessible HTML fallback.
- **Creative pack, social formats, Canva, or Runway:** read [creative templates](references/creative-templates.md). Start with the campaign brief and make deliverables reviewable before generation or export.
- **Social publishing or Meta/Google Ads:** use Windsor.ai only after its account is connected. Discover connectors and account IDs first; request confirmation immediately before any write action.

## Operating rules

1. State the deliverable, platforms, audience, aspect ratios, brand constraints, and CTA before creating a campaign asset. Ask only for missing material inputs.
2. For Three.js, use CSS for display size; update the camera projection only when the drawing buffer changes. Cap render cost for mobile and dispose of geometries, materials, textures, controls, and loaded assets on unmount.
3. Use GLTF/GLB for production 3D assets. Do not claim to have modeled a production asset unless one was actually created or supplied; keep asset licensing and attribution with the project.
4. For Canva or Runway, first verify the connected workspace/capabilities. Do not promise video generation or editing when the connected plan does not expose it. Treat credit-consuming generation as an external-cost action.
5. For Windsor.ai, first call `get_connectors`; never infer connector slugs, account IDs, action IDs, or permissions. Read analytics safely; require the user's confirmation naming the exact account and change before `execute_action`.
6. Keep raw media and intermediate renders outside Git. Save final deliverables in the user-approved location and report actual output paths or platform URLs only after verification.

## Quality gate

- Visual: safe margins, readable captions, contrast, platform-appropriate framing, and a clean first frame/thumbnail.
- Web 3D: keyboard-safe page content, `prefers-reduced-motion` fallback, no horizontal overflow, mobile performance checked.
- Marketing: correct brand/account, destination URL and UTM policy, and no unapproved claims.
- Publishing/ads: report the selected account, asset, audience, budget, schedule, and the explicit approval that authorized the write.
