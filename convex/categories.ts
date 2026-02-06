/**
 * Coding Context: Category Functions
 *
 * Query and mutation functions for managing categories.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("cod_category").order("asc").collect();
  },
});

export const getById = query({
  args: { id: v.id("cod_category") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getByParent = query({
  args: { parentId: v.optional(v.id("cod_category")) },
  handler: async (ctx, args) => {
    if (args.parentId === undefined) {
      return await ctx.db
        .query("cod_category")
        .filter((q) => q.eq(q.field("supercatid"), undefined))
        .collect();
    }
    return await ctx.db
      .query("cod_category")
      .withIndex("by_parent", (q) => q.eq("supercatid", args.parentId))
      .collect();
  },
});

export const nameExists = query({
  args: {
    name: v.string(),
    excludeId: v.optional(v.id("cod_category")),
  },
  handler: async (ctx, args) => {
    const categories = await ctx.db
      .query("cod_category")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .collect();

    if (args.excludeId) {
      return categories.some((c) => c._id !== args.excludeId);
    }
    return categories.length > 0;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const create = mutation({
  args: {
    name: v.string(),
    memo: v.optional(v.string()),
    supercatid: v.optional(v.id("cod_category")),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("cod_category", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("cod_category"),
    name: v.optional(v.string()),
    memo: v.optional(v.string()),
    supercatid: v.optional(v.id("cod_category")),
    owner: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("cod_category") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
