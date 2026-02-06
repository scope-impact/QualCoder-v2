/**
 * Cases Context: Case Functions
 *
 * Query and mutation functions for managing cases.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Case Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("cas_case").order("asc").collect();
  },
});

export const getById = query({
  args: { id: v.id("cas_case") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getByName = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const cases = await ctx.db
      .query("cas_case")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .collect();
    return cases[0] ?? null;
  },
});

export const getCasesForSource = query({
  args: { sourceId: v.id("src_source") },
  handler: async (ctx, args) => {
    const links = await ctx.db
      .query("cas_source_link")
      .filter((q) => q.eq(q.field("source_id"), args.sourceId))
      .collect();

    const cases = await Promise.all(
      links.map((link) => ctx.db.get(link.case_id))
    );

    return cases.filter((c) => c !== null);
  },
});

// =========================================================================
// Case Mutations
// =========================================================================

export const create = mutation({
  args: {
    name: v.string(),
    description: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    created_at: v.optional(v.string()),
    updated_at: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("cas_case", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("cas_case"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    updated_at: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("cas_case") },
  handler: async (ctx, args) => {
    // Delete associated source links
    const links = await ctx.db
      .query("cas_source_link")
      .filter((q) => q.eq(q.field("case_id"), args.id))
      .collect();
    for (const link of links) {
      await ctx.db.delete(link._id);
    }

    // Delete associated attributes
    const attrs = await ctx.db
      .query("cas_attribute")
      .withIndex("by_case_and_name", (q) => q.eq("case_id", args.id))
      .collect();
    for (const attr of attrs) {
      await ctx.db.delete(attr._id);
    }

    // Delete the case
    await ctx.db.delete(args.id);
  },
});

// =========================================================================
// Source Link Functions
// =========================================================================

export const linkSource = mutation({
  args: {
    caseId: v.id("cas_case"),
    sourceId: v.id("src_source"),
    sourceName: v.string(),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Check if link already exists
    const existing = await ctx.db
      .query("cas_source_link")
      .withIndex("by_case_and_source", (q) =>
        q.eq("case_id", args.caseId).eq("source_id", args.sourceId)
      )
      .first();

    if (existing) {
      return existing._id;
    }

    return await ctx.db.insert("cas_source_link", {
      case_id: args.caseId,
      source_id: args.sourceId,
      source_name: args.sourceName,
      owner: args.owner,
      date: args.date,
    });
  },
});

export const unlinkSource = mutation({
  args: {
    caseId: v.id("cas_case"),
    sourceId: v.id("src_source"),
  },
  handler: async (ctx, args) => {
    const link = await ctx.db
      .query("cas_source_link")
      .withIndex("by_case_and_source", (q) =>
        q.eq("case_id", args.caseId).eq("source_id", args.sourceId)
      )
      .first();

    if (link) {
      await ctx.db.delete(link._id);
    }
  },
});

// =========================================================================
// Attribute Functions
// =========================================================================

export const getAttributes = query({
  args: { caseId: v.id("cas_case") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cas_attribute")
      .withIndex("by_case_and_name", (q) => q.eq("case_id", args.caseId))
      .collect();
  },
});

export const saveAttribute = mutation({
  args: {
    caseId: v.id("cas_case"),
    name: v.string(),
    attrType: v.string(),
    valueText: v.optional(v.string()),
    valueNumber: v.optional(v.number()),
    valueDate: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Check if attribute already exists
    const existing = await ctx.db
      .query("cas_attribute")
      .withIndex("by_case_and_name", (q) =>
        q.eq("case_id", args.caseId).eq("name", args.name)
      )
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        attr_type: args.attrType,
        value_text: args.valueText,
        value_number: args.valueNumber,
        value_date: args.valueDate,
      });
      return existing._id;
    }

    return await ctx.db.insert("cas_attribute", {
      case_id: args.caseId,
      name: args.name,
      attr_type: args.attrType,
      value_text: args.valueText,
      value_number: args.valueNumber,
      value_date: args.valueDate,
    });
  },
});

export const deleteAttribute = mutation({
  args: {
    caseId: v.id("cas_case"),
    attributeName: v.string(),
  },
  handler: async (ctx, args) => {
    const attr = await ctx.db
      .query("cas_attribute")
      .withIndex("by_case_and_name", (q) =>
        q.eq("case_id", args.caseId).eq("name", args.attributeName)
      )
      .first();

    if (attr) {
      await ctx.db.delete(attr._id);
    }
  },
});
