/****** Object:  Table [dbo].[Customers]    Script Date: 2024-06-25 12:28:49 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Customers](
	[custID] [int] IDENTITY(1,1) NOT NULL,
	[stripeCustID] [varchar](max) NOT NULL,
	[custType] [int] NOT NULL,
	[linkedID] [int] NOT NULL,
	[subscriptDate] [datetime] NULL,
	[lastPayDate] [datetime] NULL,
	[status] [int] NOT NULL,
	[planID] [int] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

