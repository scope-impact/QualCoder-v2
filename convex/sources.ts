/**
 * Sources Context: Source Functions
 *
 * Query and mutation functions for managing sources.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("src_source").order("asc").collect();
  },
});

export const getById = query({
  args: { id: v.id("src_source") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getByName = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const sources = await ctx.db
      .query("src_source")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .collect();
    return sources[0] ?? null;
  },
});

export const getByType = query({
  args: { sourceType: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("src_source")
      .withIndex("by_type", (q) => q.eq("source_type", args.sourceType))
      .collect();
  },
});

export const getByStatus = query({
  args: { status: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("src_source")
      .withIndex("by_status", (q) => q.eq("status", args.status))
      .collect();
  },
});

export const getByFolder = query({
  args: { folderId: v.optional(v.id("src_folder")) },
  handler: async (ctx, args) => {
    if (args.folderId === undefined) {
      return await ctx.db
        .query("src_source")
        .filter((q) => q.eq(q.field("folder_id"), undefined))
        .collect();
    }
    return await ctx.db
      .query("src_source")
      .withIndex("by_folder", (q) => q.eq("folder_id", args.folderId))
      .collect();
  },
});

export const exists = query({
  args: { id: v.id("src_source") },
  handler: async (ctx, args) => {
    const source = await ctx.db.get(args.id);
    return source !== null;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const create = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("src_source", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("src_source"),
    name: v.optional(v.string()),
    fulltext: v.optional(v.string()),
    mediapath: v.optional(v.string()),
    memo: v.optional(v.string()),
    owner: v.optional(v.string()),
    source_type: v.optional(v.string()),
    status: v.optional(v.string()),
    file_size: v.optional(v.number()),
    origin: v.optional(v.string()),
    folder_id: v.optional(v.id("src_folder")),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("src_source") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
