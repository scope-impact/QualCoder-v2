/**
 * Sources Context: Folder Functions
 *
 * Query and mutation functions for managing folders.
 */

import { v } from "convex/values";
import { Id } from "./_generated/dataModel";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("src_folder").order("asc").collect();
  },
});

export const getById = query({
  args: { id: v.id("src_folder") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getChildren = query({
  args: { parentId: v.optional(v.id("src_folder")) },
  handler: async (ctx, args) => {
    if (args.parentId === undefined) {
      return await ctx.db
        .query("src_folder")
        .filter((q) => q.eq(q.field("parent_id"), undefined))
        .collect();
    }
    return await ctx.db
      .query("src_folder")
      .withIndex("by_parent", (q) => q.eq("parent_id", args.parentId))
      .collect();
  },
});

export const getRootFolders = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("src_folder")
      .filter((q) => q.eq(q.field("parent_id"), undefined))
      .collect();
  },
});

export const getDescendants = query({
  args: { folderId: v.id("src_folder") },
  handler: async (ctx, args) => {
    const descendants: Array<{
      _id: Id<"src_folder">;
      name: string;
      parent_id?: Id<"src_folder">;
      created_at?: string;
    }> = [];

    const collectDescendants = async (parentId: Id<"src_folder">) => {
      const children = await ctx.db
        .query("src_folder")
        .withIndex("by_parent", (q) => q.eq("parent_id", parentId))
        .collect();

      for (const child of children) {
        descendants.push(child);
        await collectDescendants(child._id);
      }
    };

    await collectDescendants(args.folderId);
    return descendants;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const create = mutation({
  args: {
    name: v.string(),
    parent_id: v.optional(v.id("src_folder")),
    created_at: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("src_folder", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("src_folder"),
    name: v.optional(v.string()),
    parent_id: v.optional(v.id("src_folder")),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    await ctx.db.patch(id, updates);
  },
});

export const remove = mutation({
  args: { id: v.id("src_folder") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const updateParent = mutation({
  args: {
    folderId: v.id("src_folder"),
    newParentId: v.optional(v.id("src_folder")),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.folderId, { parent_id: args.newParentId });
  },
});
