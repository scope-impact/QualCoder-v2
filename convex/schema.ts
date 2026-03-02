/**
 * QualCoder Convex Database Schema
 *
 * Defines all tables mirroring the SQLite schema structure.
 * Uses bounded context prefixes for table isolation.
 */

import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // =========================================================================
  // Coding Context Tables (cod_)
  // =========================================================================

  cod_category: defineTable({
    name: v.string(),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
    supercatid: v.optional(v.id("cod_category")),
  })
    .index("by_name", ["name"])
    .index("by_parent", ["supercatid"]),

  cod_code: defineTable({
    name: v.string(),
    color: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
    catid: v.optional(v.id("cod_category")),
  })
    .index("by_name", ["name"])
    .index("by_category", ["catid"]),

  cod_segment: defineTable({
    cid: v.id("cod_code"),
    fid: v.id("src_source"),
    pos0: v.number(),
    pos1: v.number(),
    seltext: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
    important: v.optional(v.number()),
    source_name: v.optional(v.string()),
  })
    .index("by_code", ["cid"])
    .index("by_source", ["fid"])
    .index("by_source_and_code", ["fid", "cid"]),

  // =========================================================================
  // Sources Context Tables (src_)
  // =========================================================================

  src_folder: defineTable({
    name: v.string(),
    parent_id: v.optional(v.id("src_folder")),
    created_at: v.optional(v.string()),
  })
    .index("by_name", ["name"])
    .index("by_parent", ["parent_id"]),

  src_source: defineTable({
    name: v.string(),
    fulltext: v.optional(v.string()),
    mediapath: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
    av_text_id: v.optional(v.number()),
    risession: v.optional(v.number()),
    source_type: v.optional(v.string()),
    status: v.optional(v.string()),
    file_size: v.optional(v.number()),
    origin: v.optional(v.string()),
    folder_id: v.optional(v.id("src_folder")),
  })
    .index("by_name", ["name"])
    .index("by_type", ["source_type"])
    .index("by_folder", ["folder_id"])
    .index("by_status", ["status"]),

  // =========================================================================
  // Cases Context Tables (cas_)
  // =========================================================================

  cas_case: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    created_at: v.optional(v.string()),
    updated_at: v.optional(v.string()),
  }).index("by_name", ["name"]),

  cas_attribute: defineTable({
    case_id: v.id("cas_case"),
    name: v.string(),
    attr_type: v.string(),
    value_text: v.optional(v.string()),
    value_number: v.optional(v.number()),
    value_date: v.optional(v.string()),
  }).index("by_case_and_name", ["case_id", "name"]),

  cas_source_link: defineTable({
    case_id: v.id("cas_case"),
    source_id: v.id("src_source"),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
    source_name: v.optional(v.string()),
  }).index("by_case_and_source", ["case_id", "source_id"]),

  // =========================================================================
  // Projects Context Tables (prj_)
  // =========================================================================

  prj_settings: defineTable({
    key: v.string(),
    value: v.optional(v.string()),
    updated_at: v.optional(v.string()),
  }).index("by_key", ["key"]),
});
