/**
 * Coding Context: Segment Functions
 *
 * Query and mutation functions for managing text segments.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("cod_segment").collect();
  },
});

export const getById = query({
  args: { id: v.id("cod_segment") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getBySource = query({
  args: { sourceId: v.id("src_source") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cod_segment")
      .withIndex("by_source", (q) => q.eq("fid", args.sourceId))
      .collect();
  },
});

export const getByCode = query({
  args: { codeId: v.id("cod_code") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cod_segment")
      .withIndex("by_code", (q) => q.eq("cid", args.codeId))
      .collect();
  },
});

export const getBySourceAndCode = query({
  args: {
    sourceId: v.id("src_source"),
    codeId: v.id("cod_code"),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cod_segment")
      .withIndex("by_source_and_code", (q) =>
        q.eq("fid", args.sourceId).eq("cid", args.codeId)
      )
      .collect();
  },
});

export const countByCode = query({
  args: { codeId: v.id("cod_code") },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_code", (q) => q.eq("cid", args.codeId))
      .collect();
    return segments.length;
  },
});

export const countBySource = query({
  args: { sourceId: v.id("src_source") },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_source", (q) => q.eq("fid", args.sourceId))
      .collect();
    return segments.length;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const create = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("cod_segment", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("cod_segment"),
    cid: v.optional(v.id("cod_code")),
    fid: v.optional(v.id("src_source")),
    pos0: v.optional(v.number()),
    pos1: v.optional(v.number()),
    seltext: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    important: v.optional(v.number()),
    source_name: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("cod_segment") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const deleteByCode = mutation({
  args: { codeId: v.id("cod_code") },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_code", (q) => q.eq("cid", args.codeId))
      .collect();

    for (const segment of segments) {
      await ctx.db.delete(segment._id);
    }

    return segments.length;
  },
});

export const deleteBySource = mutation({
  args: { sourceId: v.id("src_source") },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_source", (q) => q.eq("fid", args.sourceId))
      .collect();

    for (const segment of segments) {
      await ctx.db.delete(segment._id);
    }

    return segments.length;
  },
});

export const reassignCode = mutation({
  args: {
    fromCodeId: v.id("cod_code"),
    toCodeId: v.id("cod_code"),
  },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_code", (q) => q.eq("cid", args.fromCodeId))
      .collect();

    for (const segment of segments) {
      await ctx.db.patch(segment._id, { cid: args.toCodeId });
    }

    return segments.length;
  },
});

export const updateSourceName = mutation({
  args: {
    sourceId: v.id("src_source"),
    newName: v.string(),
  },
  handler: async (ctx, args) => {
    const segments = await ctx.db
      .query("cod_segment")
      .withIndex("by_source", (q) => q.eq("fid", args.sourceId))
      .collect();

    for (const segment of segments) {
      await ctx.db.patch(segment._id, { source_name: args.newName });
    }
  },
});
