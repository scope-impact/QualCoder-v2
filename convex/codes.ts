/**
 * Coding Context: Code Functions
 *
 * Query and mutation functions for managing codes.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("cod_code").order("asc").collect();
  },
});

export const getById = query({
  args: { id: v.id("cod_code") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getByName = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const codes = await ctx.db
      .query("cod_code")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .collect();
    return codes[0] ?? null;
  },
});

export const getByCategory = query({
  args: { categoryId: v.optional(v.id("cod_category")) },
  handler: async (ctx, args) => {
    if (args.categoryId === undefined) {
      return await ctx.db
        .query("cod_code")
        .filter((q) => q.eq(q.field("catid"), undefined))
        .collect();
    }
    return await ctx.db
      .query("cod_code")
      .withIndex("by_category", (q) => q.eq("catid", args.categoryId))
      .collect();
  },
});

export const exists = query({
  args: { id: v.id("cod_code") },
  handler: async (ctx, args) => {
    const code = await ctx.db.get(args.id);
    return code !== null;
  },
});

export const nameExists = query({
  args: {
    name: v.string(),
    excludeId: v.optional(v.id("cod_code")),
  },
  handler: async (ctx, args) => {
    const codes = await ctx.db
      .query("cod_code")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .collect();

    if (args.excludeId) {
      return codes.some((c) => c._id !== args.excludeId);
    }
    return codes.length > 0;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const create = mutation({
  args: {
    name: v.string(),
    color: v.optional(v.string()),
    memo: v.optional(v.string()),
    catid: v.optional(v.id("cod_category")),
    owner: v.optional(v.string()),
    date: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("cod_code", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("cod_code"),
    name: v.optional(v.string()),
    color: v.optional(v.string()),
    memo: v.optional(v.string()),
    catid: v.optional(v.id("cod_category")),
    owner: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("cod_code") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
